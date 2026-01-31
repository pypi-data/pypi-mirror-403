from datetime import date, datetime
from typing import Self

from httpx import Response
from loguru import logger

from bb_integrations_lib.gravitate.base_api import BaseAPI
from bb_integrations_lib.secrets.credential_models import SamsaraCredential


class SamsaraClient(BaseAPI):
    """Client for Samsara Fleet API.

    Uses Bearer token authentication with a static API token.
    """

    def __init__(self, base_url: str, api_token: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def __repr__(self) -> str:
        return "Samsara Fleet API client"

    @classmethod
    def from_credential(cls, credential: SamsaraCredential) -> Self:
        return cls(
            base_url=credential.base_url,
            api_token=credential.api_token,
        )

    async def _auth_request(self, method: str, **kwargs) -> Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.api_token}"
        headers["Content-Type"] = "application/json"
        kwargs["headers"] = headers
        kwargs["url"] = f"{self.base_url}{kwargs.get('url', '')}"
        kwargs["timeout"] = kwargs.get("timeout", 90)

        return await getattr(self, method)(**kwargs)

    async def auth_get(self, **kwargs) -> Response:
        return await self._auth_request("get", **kwargs)

    async def auth_post(self, **kwargs) -> Response:
        return await self._auth_request("post", **kwargs)

    async def get_hos_clocks(self, driver_ids: list[str]) -> Response:
        """
        Get real-time HOS clocks for drivers.

        Returns remaining drive time, shift time, and cycle time.

        GET /fleet/hos/clocks?driverIds={comma_separated_ids}

        Args:
            driver_ids: List of Samsara driver IDs

        Returns:
            Response containing HOS clock data for each driver
        """
        params = {"driverIds": ",".join(driver_ids)}
        response = await self.auth_get(url="/fleet/hos/clocks", params=params)
        response.raise_for_status()
        return response

    async def get_hos_daily_logs(
        self,
        driver_ids: list[str],
        start_date: date,
        end_date: date,
    ) -> Response:
        """
        Get HOS daily logs for drivers.

        Returns duty period start/end times, cycle info, distance traveled,
        and ELD settings including cycle type (7-day vs 8-day).

        GET /fleet/hos/daily-logs?driverIds={ids}&startDate={date}&endDate={date}

        Args:
            driver_ids: List of Samsara driver IDs
            start_date: Start date for log query (inclusive)
            end_date: End date for log query (inclusive)

        Returns:
            Response containing daily log data for each driver
        """
        params = {
            "driverIds": ",".join(driver_ids),
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }
        response = await self.auth_get(url="/fleet/hos/daily-logs", params=params)
        response.raise_for_status()
        return response

    async def get_hos_logs(
        self,
        driver_ids: list[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Response:
        """
        Get individual HOS log segments for drivers.

        Returns log entries with dutyStatus, startTime, endTime for each segment.
        Used to determine the legal duty period start (first ON_DUTY after 10+ hours off).

        GET /fleet/hos/logs?driverIds={ids}&startTime={iso}&endTime={iso}

        Args:
            driver_ids: List of Samsara driver IDs
            start_time: Start time for log query (ISO format)
            end_time: End time for log query (ISO format)

        Returns:
            Response containing HOS log segments for each driver
        """
        params = {
            "driverIds": ",".join(driver_ids),
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
        }
        response = await self.auth_get(url="/fleet/hos/logs", params=params)
        response.raise_for_status()
        return response