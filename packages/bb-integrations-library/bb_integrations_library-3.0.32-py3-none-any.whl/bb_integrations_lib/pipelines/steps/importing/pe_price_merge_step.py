import json
from typing import List

from loguru import logger

from bb_integrations_lib.gravitate.pe_api import GravitatePEAPI
from bb_integrations_lib.models.pipeline_structs import BBDUploadResult, UploadResult
from bb_integrations_lib.models.rita.issue import IssueBase, IssueCategory
from bb_integrations_lib.protocols.flat_file import PePriceMergeIntegration
from bb_integrations_lib.protocols.pipelines import Step
from bb_integrations_lib.util.utils import CustomJSONEncoder


class PEPriceMerge(Step):
    def __init__(
            self,
            pe_client: GravitatePEAPI,
            *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.pe_client = pe_client

    def describe(self) -> str:
        return "Merge Prices in Pricing Engine"

    async def execute(self, i: List[PePriceMergeIntegration]) -> BBDUploadResult:
        failed_rows: List = []
        success_rows: List = []
        responses: List = []
        try:
            for row in i:
                row_dump = row.model_dump(exclude_none=True)
                try:
                    response = await self.pe_client.merge_prices(row_dump)
                    response_data = response.json()
                    success_rows.append({**row_dump, "response": response_data})
                    responses.append(response_data)
                except Exception as e:
                    logger.error(f"Failed to merge row: {e}")
                    failed_rows.append(row_dump)
                    continue
        except Exception as e:
            logger.error(f"Failed to merge rows: {e}")
            raise e

        logs = {
            "request": [l.model_dump() for l in i],
            "response": responses
        }
        self.pipeline_context.included_files["merge prices logs"] = json.dumps(logs, cls=CustomJSONEncoder)
        return UploadResult(succeeded=len(success_rows), failed=len(failed_rows),
                            succeeded_items=list(success_rows))

