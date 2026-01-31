import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, AsyncIterator

import pytz
from loguru import logger

from bb_integrations_lib.gravitate.rita_api import GravitateRitaAPI
from bb_integrations_lib.protocols.pipelines import GeneratorStep
from bb_integrations_lib.provider.ftp.client import FTPIntegrationClient
from bb_integrations_lib.secrets.credential_models import FTPCredential
from bb_integrations_lib.provider.ftp.model import FTPType
from bb_integrations_lib.shared.model import RawData, FileConfigRawData, ConfigMode, ConfigMatchMode
from bb_integrations_lib.util.utils import check_if_file_greater_than_date, file_exact_match


class SFTPFileConfigStep(GeneratorStep):

    def __init__(self, rita_client: GravitateRitaAPI,
                 ftp_client: FTPIntegrationClient | dict[str, FTPIntegrationClient],
                 mode: ConfigMode,
                 match_mode: ConfigMatchMode = ConfigMatchMode.Partial,
                 bucket_name: str | None = None,
                 config_name: str | None = None,
                 min_date: datetime = None,
                 min_date_tz: pytz.BaseTzInfo | None = None,
                 minutes_back: int | None = None,
                 strip_trailing_digits: bool = False,
                 use_server_modified_date: bool = False,
                 *args,
                 **kwargs) -> None:
        """
        Imports SFTP files based on the provided or discovered fileconfigs.

        :param rita_client: The RITA client to use to retrieve fileconfigs.
        :param ftp_client: The FTP client, or a dict of FTP clients with keys matching confignames, to use to retrieve
          data.
        :param mode: How the step should discover fileconfigs.
        :param match_mode: How the step should match fileconfigs to various properties of the files being scanned.
        :param bucket_name: The bucket name which holds fileconfigs, for FromBucket and ByName modes.
        :param config_name: The fileconfig name, if using ByName mode.
        :param min_date: Filter out files with a date before this.
        :param use_server_modified_date: If True and connection is SFTP, use server's file
          modification time instead of parsing date from filename. Falls back to filename
          parsing for FTP connections or if server date unavailable.
        """
        super().__init__(*args, **kwargs)
        self.rita_client = rita_client
        self.ftp_client = ftp_client
        self.mode = mode

        self.match_mode = match_mode
        self.strip_trailing_digits = strip_trailing_digits
        self.bucket_name = bucket_name
        self.config_name = config_name
        self.min_date = min_date
        self.min_date_tz = min_date_tz
        self.minutes_back = minutes_back
        self.use_server_modified_date = use_server_modified_date
        self.file_configs: dict[str, Any] = {}

        if self.mode == ConfigMode.FromBucket and not self.bucket_name:
            raise ValueError("Cannot use FromBucket mode without setting a bucket_name")
        if self.mode == ConfigMode.ByName and not self.bucket_name:
            raise ValueError("Cannot use ByName mode without setting a bucket_name")
        if self.mode == ConfigMode.ByName and not self.config_name:
            raise ValueError("Cannot use ByName mode without setting a config_name")

    async def load_file_configs(self):
        if self.mode == ConfigMode.AllFiltered:
            self.file_configs = await self.rita_client.get_file_configs()
        elif self.mode == ConfigMode.FromBucket:
            self.file_configs = await self.rita_client.get_fileconfigs_from_bucket(self.bucket_name)
        elif self.mode == ConfigMode.ByName:
            self.file_configs = await self.rita_client.get_fileconfig_by_name(self.bucket_name, self.config_name)
        logger.info(f"Loaded {len(self.file_configs)} fileconfigs: {self.config_name}")

    def describe(self) -> str:
        return "Importing SFTP files based on file configs"

    async def setup(self):
        if self.min_date is None:
            if self.pipeline_context and self.pipeline_context.max_sync:
                self.min_date = self.pipeline_context.max_sync.max_sync_date
            else:
                self.min_date = datetime.now(tz=self.min_date_tz)

        if self.minutes_back is not None:
            self.min_date -= timedelta(minutes=self.minutes_back)

    def file_modified_after_min_date(
        self,
        file_path: str,
        file_name: str,
        file_config: Any,
        ftp_client: FTPIntegrationClient
    ) -> bool:
        """
        Check if file was modified after min_date.

        Uses server modification time for SFTP when use_server_modified_date=True,
        otherwise falls back to parsing date from filename.

        :returns: True if file should be included (modified after min_date or no date check applies)
        """
        if not self.min_date:
            return True

        # Try server modification time (SFTP only)
        if self.use_server_modified_date:
            if ftp_client.credentials.ftp_type == FTPType.sftp:
                file_info = ftp_client.get_file_info(file_path)
                if file_info.last_modification_time:
                    file_mtime = datetime.fromtimestamp(file_info.last_modification_time, tz=pytz.UTC)
                    is_newer = file_mtime > self.min_date
                    if not is_newer:
                        logger.debug(f"Skipping {file_name}: server mtime {file_mtime} UTC < {self.min_date} {self.min_date_tz}")
                    return is_newer
            else:
                logger.warning(
                    f"use_server_modified_date=True but connection is {ftp_client.credentials.ftp_type}, "
                    "falling back to filename parsing"
                )

        # Fallback: parse date from filename
        if file_config.date_format != "":
            is_newer = check_if_file_greater_than_date(
                file_name, file_config.file_name, file_config.date_format,
                self.min_date, self.strip_trailing_digits, self.min_date_tz
            )
            if not is_newer:
                logger.debug(f"Skipping {file_name}: filename date <= {self.min_date}")
            return is_newer

        # No date check applies
        return True

    async def generator(self, i: Any) -> AsyncIterator[RawData]:
        await self.load_file_configs()

        for config_name, file_config in self.file_configs.items():
            if isinstance(self.ftp_client, dict):
                selected_ftp_client = self.ftp_client[config_name]
            else:
                selected_ftp_client = self.ftp_client
            logger.info(f"Scanning with fileconfig '{config_name}' in directory {file_config.inbound_directory}")
            file_names = list(selected_ftp_client.list_files(file_config.inbound_directory))
            for idx, file_name in enumerate(file_names):
                if self.match_mode == ConfigMatchMode.Exact:
                    logger.info(f"Exact Matching file {file_name}")
                    if not file_exact_match(file_name, file_config.file_name):
                        logger.debug(f"Skipping file {file_name} due to not matching exactly to {file_config.file_name}")
                        continue
                elif self.match_mode == ConfigMatchMode.Partial:
                    if not file_config.file_name in file_name:
                        continue
                elif self.match_mode == ConfigMatchMode.ByExtension:
                    if not file_name.endswith(file_config.file_extension):
                        continue
                file_path = str(Path(file_config.inbound_directory) / file_name)
                if not self.file_modified_after_min_date(file_path, file_name, file_config, selected_ftp_client):
                    continue
                logger.info(f"fetching {idx+1}/{len(file_names)}: {file_name}")
                rd = selected_ftp_client.download_file(file_path)
                self.pipeline_context.file_config = file_config
                yield FileConfigRawData(data=rd.data, file_name=rd.file_name, file_config=file_config)




if __name__ == "__main__":
    async def main():
        s = SFTPFileConfigStep(
            rita_client=GravitateRitaAPI(
                base_url="",
                username="",
                password=""
            ),
            ftp_client=FTPIntegrationClient(
                credentials=FTPCredential(
                    host="",
                    username="",
                    password="",
                    port=22,
                    ftp_type=FTPType.sftp
                ),
            ),
            mode=ConfigMode.ByName,
            config_name="my_config"
        )
        async for r in s.generator(None):
            print(r)

    asyncio.run(main())