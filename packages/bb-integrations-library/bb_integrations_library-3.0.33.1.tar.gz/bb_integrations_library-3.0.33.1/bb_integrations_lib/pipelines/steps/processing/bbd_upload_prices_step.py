import json
from math import ceil
from time import sleep
from typing import Iterable, Union

from loguru import logger
from more_itertools import chunked

from bb_integrations_lib.gravitate.sd_api import GravitateSDAPI
from bb_integrations_lib.protocols.flat_file import PriceRow
from bb_integrations_lib.protocols.pipelines import Step
from bb_integrations_lib.shared.model import SupplyPriceUpdateManyRequest


class BBDUploadPricesStep(Step):
    def __init__(self, sd_client: GravitateSDAPI, sleep_between: float = 0.5, chunk_size: int = 1000, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sd_client = sd_client
        self.sleep_between = sleep_between
        self.chunk_size = chunk_size

    def describe(self) -> str:
        return "Upload prices to BBD"

    def remove_duplicates(self, price_dump: list[dict]) -> tuple[list[dict], list[dict]]:
        seen = {}
        removed_duplicates = []
        for record in price_dump:
            key = json.dumps(record, sort_keys=True)
            if key in seen:
                removed_duplicates.append(record)
            else:
                seen[key] = record
        return list(seen.values()), removed_duplicates

    async def execute(self, i: Union[Iterable[PriceRow], Iterable[SupplyPriceUpdateManyRequest]]) -> int:
        attempted = 0
        succeeded = 0
        responses = []
        price_dump = [item.model_dump(mode="json") for item in i]
        self.pipeline_context.included_files["sd_request_original"] = json.dumps(price_dump)
        deduped_prices, removed_duplicates = self.remove_duplicates(price_dump)
        logger.info(f"De duplicated prices to size: {len(deduped_prices)} from size: {len(price_dump)}")
        if removed_duplicates:
            logger.info(f"Removed {len(removed_duplicates)} duplicate prices")
            self.pipeline_context.included_files["excluded_prices"] = json.dumps(removed_duplicates)
        count = ceil(len(deduped_prices) / self.chunk_size)
        for idx, group in enumerate(chunked(deduped_prices, self.chunk_size)):
            logger.info(f"Uploading prices to bestbuy {idx + 1} of {count}")
            sleep(self.sleep_between)
            attempted += len(group)
            try:
                successes, response = await self.sd_client.upload_prices(group)
                succeeded += successes
                responses.append(response)
            except Exception as e:
                logger.error(f"Batch {idx} prices failed | {e}")
                continue
        logger.info(f"Successfully uploaded {succeeded} prices to BBD.")
        logs = {
            "response": responses,
            "attempted": attempted,
            "succeeded": succeeded
        }
        self.pipeline_context.included_files["sd_request_deduped"] = json.dumps(deduped_prices)
        self.pipeline_context.included_files["sd_upload_response"] = json.dumps(logs)
        return succeeded
