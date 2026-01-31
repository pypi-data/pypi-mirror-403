import json
from datetime import datetime, timedelta, UTC
from functools import lru_cache
from itertools import groupby
from typing import Dict, Any, List, Tuple, Optional

import pytz
from dateutil.parser import parse
from more_itertools.more import chunked

from bb_integrations_lib.gravitate.pe_api import GravitatePEAPI
from bb_integrations_lib.gravitate.rita_api import GravitateRitaAPI
from bb_integrations_lib.mappers.prices.model import PricePublisher, PricingIntegrationConfig
from bb_integrations_lib.models.pipeline_structs import StopPipeline, NoPipelineData
from bb_integrations_lib.models.rita.config import GenericConfig
from bb_integrations_lib.protocols.pipelines import Step, ParserBase
from bb_integrations_lib.shared.model import PEPriceData


class ImpossibleToParseDate(Exception):
    pass


class PEPriceExportStep(Step):
    def __init__(self,
                 rita_client: GravitateRitaAPI,
                 pe_client: GravitatePEAPI,
                 price_publishers: list[PricePublisher],
                 parser: type[ParserBase] | None = None,
                 parser_kwargs: dict | None = None,
                 hours_back: int = 24,
                 max_sync_id_override: int | None = None,
                 addl_endpoint_args: dict | None = None,
                 last_sync_date: datetime | None = None,
                 *args, **kwargs):
        """This step requires:
            - tenant_name: [REQUIRED] client name. (i.e Jacksons, TTE, Coleman)
            - price_publishers:[REQUIRED] a list of price publisher names to be included in the price request
            - config_id: [OPTIONAL] a RITA config to pull last sync date
            - hours_back: [OPTIONAL] hours back from last sync date, defaults to 12
            - mode: [OPTIONAL] can be 'production' or 'development', defaults to production
        """
        super().__init__(*args, **kwargs)
        self.pe_client = pe_client
        self.price_publishers = price_publishers
        self.hours_back = hours_back
        self.rita_client = rita_client
        self.additional_endpoint_arguments = addl_endpoint_args or {}
        self.last_sync_date = last_sync_date
        self.max_sync_id_override = max_sync_id_override
        self.max_sync_pk_id = 0
        if parser:
            self.custom_parser = parser
            self.custom_parser_kwargs = parser_kwargs or {}

    def price_publisher_lkp(self) -> Dict[str, PricePublisher]:
        lkp = {}
        pp = self.price_publishers
        for p in pp:
            lkp[p.name] = p
        return lkp

    def get_publisher_contract_id(self, key: str, actual_contract_id: str | int) -> str | None:
        lkp = self.price_publisher_lkp()
        pub = lkp[key]
        if pub.contract_id_override:
            return pub.contract_id_override
        if pub.use_contract_id:
            return actual_contract_id
        return None

    def get_publisher_extend_by(self, key: str) -> int | None:
        lkp = self.price_publisher_lkp()
        return lkp[key].extend_by_days

    def get_publisher_price_type(self, key: str) -> str:
        lkp = self.price_publisher_lkp()
        return lkp[key].price_type

    def price_type_rows(self, rows: List[PEPriceData]) -> List[PEPriceData]:
        for row in rows:
            price_type = self.get_publisher_price_type(row.PricePublisher)
            row.PriceType = price_type
        return rows

    def describe(self) -> str:
        return f"Export Pricing Engine Prices"

    async def setup(self):
        if self.last_sync_date is not None:
            return

        max_sync = self.pipeline_context.max_sync if self.pipeline_context else None
        if not max_sync:
            return

        pe_max_sync = (max_sync.context or {}).get('pe_max_sync', {})
        max_sync_datetime = pe_max_sync.get('MaxSyncDateTime')
        if max_sync_datetime:
            self.last_sync_date = parse(max_sync_datetime)
        else:
            self.last_sync_date = max_sync.max_sync_date
        self.max_sync_pk_id = pe_max_sync.get('MaxSyncPkId', 0)

    async def execute(self, _: Any = None) -> List[PEPriceData] | List[Dict]:
        updated_prices = await self.get_updated_prices_for_publishers(last_sync_date=self.last_sync_date,
                                                                      price_publishers=self.price_publishers)
        if not updated_prices:
            raise NoPipelineData("No updated prices found")

        prices = self.update_historical_prices(updated_prices)
        if not hasattr(self, "custom_parser"):
            return prices
        else:
            parser = self.custom_parser(**self.custom_parser_kwargs)
            parser_results = await parser.parse(prices)
            return parser_results

    def update_historical_prices(self, rows: List[PEPriceData]) -> List[PEPriceData]:
        _sorted_id = sorted(rows, key=lambda r: (r.PriceInstrumentId, r.EffectiveFromDateTime), reverse=True)
        for instrument_id, group in groupby(_sorted_id, key=lambda r: r.PriceInstrumentId):
            group_list = PEPriceExportStep.rank_rows(list(group))
            group_list_price_typed = self.price_type_rows(group_list)
            max_row = max(group_list_price_typed, key=lambda r: r.EffectiveFromDateTime)
            max_row.ExtendByDays = self.get_publisher_extend_by(max_row.PricePublisher)
            max_row.ContractId = self.get_publisher_contract_id(max_row.PricePublisher, max_row.SourceContractId)
            max_row.IsLatest = True
        return _sorted_id

    async def get_prices(
            self,
            query: Dict,
            count: int = 1000,
            include_source_data: bool = True
    ) -> List[PEPriceData]:
        payloads = []
        records = []
        max_sync = None
        payload = {
            "Query": {**query,
                      "COUNT": count
                      },
            "includeSourceData": include_source_data
        }
        resp = await self.pe_client.get_prices(payload)
        payloads.append(payload)
        json_resp = resp.json()
        while len(json_resp['Data']) > 0:
            records.extend(json_resp['Data'])
            max_sync = json_resp["MaxSyncResult"]
            if max_sync is None:
                break
            payload["Query"]["MaxSync"] = max_sync
            payloads.append(payload)
            resp = await self.pe_client.get_prices(payload)
            json_resp = resp.json()
        self.pipeline_context.included_files["pe_response"] = json.dumps(records)
        self.pipeline_context.included_files["pe_payloads"] = json.dumps(payloads)
        if max_sync is not None:
            self.pipeline_context.extra_data['pe_max_sync'] = json.dumps(max_sync)
        return [PEPriceData.model_validate(price) for price in records]

    async def get_updated_prices_for_publishers(self,
                                                last_sync_date: datetime,
                                                price_publishers: List[PricePublisher] = None) -> List[PEPriceData]:
        max_sync_date = (last_sync_date - timedelta(hours=self.hours_back)).replace(tzinfo=pytz.UTC)
        payload = {
            "IsActiveFilterType": "ActiveOnly",
            "PricePublisherNames": [p.name for p in (price_publishers or [])],
            "MaxSync": {
                "MaxSyncDateTime": max_sync_date.isoformat(),
                "MaxSyncPkId": self.max_sync_id_override if self.max_sync_id_override is not None else self.max_sync_pk_id
            },
            **self.additional_endpoint_arguments,
        }
        rows = await self.get_prices(query=payload, include_source_data=True)
        return rows

    @staticmethod
    def rank_rows(rows: List[PEPriceData]) -> List[PEPriceData]:
        for idx, row in enumerate(rows):
            row.Rank = idx + 1
        return rows

    @staticmethod
    def try_to_parse_date(dt_string: str) -> datetime:
        if isinstance(dt_string, str):
            try:
                parsed_datetime = parse(dt_string)
                return parsed_datetime
            except (ValueError, TypeError):
                raise ImpossibleToParseDate(f"Could not parse date: {dt_string}")
        elif isinstance(dt_string, datetime):
            return dt_string
        else:
            raise ImpossibleToParseDate(f"Could not parse date: {dt_string} -> Format not supported")
