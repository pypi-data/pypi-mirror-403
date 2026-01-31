import json
from typing import List

from loguru import logger

from bb_integrations_lib.gravitate.pe_api import GravitatePEAPI
from bb_integrations_lib.models.pipeline_structs import UploadResult
from bb_integrations_lib.protocols.flat_file import PeBulkSyncIntegration
from bb_integrations_lib.protocols.pipelines import Step
from bb_integrations_lib.util.utils import CustomJSONEncoder


class PEBulksSyncPriceStructure(Step):
    def __init__(self, pe_client: GravitatePEAPI, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pe_client = pe_client

    def describe(self) -> str:
        return "Bulk Sync Price Structure in Pricing Engine"

    async def execute(self, i: List[PeBulkSyncIntegration]) -> UploadResult:
        failed_rows: List = []
        success_rows: List = []
        responses: List = []
        try:
            for row in i:
                row_dump = row.model_dump(exclude_none=True)
                row_dump = self.gen_unique_price_dtos(row_dump)
                try:
                    response = await self.pe_client.bulk_sync_price_structure(row_dump)
                    response_data = response.json()
                    responses.append(response_data)
                    success_rows.append({**row_dump, "response": response_data})
                except Exception as e:
                    logger.error(f"Failed to bulk sync row: {e}")
                    failed_rows.append({**row_dump, "response": str(e)})
                    continue
        except Exception as e:
            logger.error(f"Failed to bulk sync rows: {e}")
            raise e

        logs = {
            "request": [l.model_dump() for l in i],
            "response": responses
        }
        self.pipeline_context.included_files["bulk sync logs"] = json.dumps(logs, cls=CustomJSONEncoder)
        return UploadResult(succeeded=len(success_rows), failed=len(failed_rows),
                               succeeded_items=list(success_rows))

    def gen_unique_price_dtos(self, row_dump: dict):
        deduped = []
        keys = set()
        for elem in row_dump['IntegrationDtos'][0]['PriceInstrumentDTOs']:
            product = elem.get('ProductLookup', {}).get('SourceIdString', '')
            location = elem.get('LocationLookup', {}).get('SourceIdString', '')
            counterparty = elem.get('CounterPartyLookup', {}).get('SourceIdString', '')
            instrument = elem.get('SourceIdString', '')
            key = f"{product} @ {location} - {counterparty} | {instrument}"
            if key in keys:
                continue
            keys.add(key)
            deduped.append(elem)
        row_dump['IntegrationDtos'][0]['PriceInstrumentDTOs'] = deduped
        return row_dump
