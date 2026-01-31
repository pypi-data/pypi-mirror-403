import json
from datetime import datetime

import pytz
from bb_integrations_lib.gravitate.rita_api import GravitateRitaAPI
from bb_integrations_lib.models.rita.config import MaxSync
from bb_integrations_lib.protocols.pipelines import Step
from loguru import logger
from typing import Any


class UpdateMaxSyncContextStep(Step):
    def __init__(self, rita_client: GravitateRitaAPI, config_id: str,
                 sync_date_tz: pytz.BaseTzInfo | None = None, *args, **kwargs):
        """
        Updates the max_sync context for a config, preserving the sync date.
        Used as a final step to persist pe_max_sync context after pipeline completion.

        :param rita_client: RITA API client
        :param config_id: The config ID to update max_sync for
        :param sync_date_tz: Timezone of MaxSyncDateTime in pe_max_sync. If provided,
            converts the date from this timezone to UTC.
        """
        super().__init__(*args, **kwargs)
        self.rita_client = rita_client
        self.config_id = config_id
        self.sync_date_tz = sync_date_tz

    def describe(self) -> str:
        return "Update Max Sync Context"

    async def execute(self, i: Any = None) -> Any:
        max_sync = self.pipeline_context.max_sync if self.pipeline_context else None
        if not max_sync:
            logger.warning("No max_sync available in pipeline context")
            return i

        # Get pe_max_sync from pipeline's extra_data (set by PEPriceExportStep)
        pe_max_sync = self.pipeline_context.extra_data.get('pe_max_sync')
        if not pe_max_sync:
            logger.warning("No pe_max_sync found in pipeline extra_data")
            return i

        updated_context = max_sync.context.copy() if max_sync.context else {}
        pe_max_sync_data = json.loads(pe_max_sync)

        if self.sync_date_tz and pe_max_sync_data.get('MaxSyncDateTime'):
            naive_dt = datetime.fromisoformat(pe_max_sync_data['MaxSyncDateTime'])
            if naive_dt.tzinfo is None:
                utc_dt = self.sync_date_tz.localize(naive_dt).astimezone(pytz.UTC)
                pe_max_sync_data['MaxSyncDateTime'] = utc_dt.isoformat()

        updated_context['pe_max_sync'] = pe_max_sync_data

        updated_max_sync = MaxSync(
            max_sync_date=max_sync.max_sync_date,
            context=updated_context
        )

        await self.rita_client.update_config_max_sync(
            config_id=self.config_id,
            max_sync=updated_max_sync
        )
        logger.success(f"Updated max_sync context for config {self.config_id}")

        return i
