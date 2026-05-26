import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from curl_cffi.requests import AsyncSession
from .api_client.client import DtekClient
from .api_client.browser_auth import get_cleared_cookies
from .api_client.exceptions import DtekClientError

from .const import DOMAIN, UPDATE_INTERVAL, SITE_URLS

_LOGGER = logging.getLogger(__name__)

class DtekUpdateCoordinator(DataUpdateCoordinator):
    """Реалізація DataUpdateCoordinator для отримання даних від DTEK."""

    def __init__(self, hass: HomeAssistant, site_key: str, city: str, street: str, house: str):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.site_key = site_key
        self.city = city
        self.street = street
        self.house = house
        self.base_url = SITE_URLS.get(site_key)

    async def _async_update_data(self):
        """Отримання даних з проходженням WAF."""
        
        if not self.base_url:
            raise UpdateFailed(f"Невідомий site_key: {self.site_key}")

        try:
            # 1. Проходимо WAF та отримуємо сирі куки через Playwright
            schedule_url = f"{self.base_url}/ua/shutdowns"
            _LOGGER.debug("Проходження WAF для %s", schedule_url)
            raw_cookies, csrf_token = await get_cleared_cookies(schedule_url)
            cookies_dict = {}
            if isinstance(raw_cookies, list):
                cookies_dict = {cookie["name"]: cookie["value"] for cookie in raw_cookies}
            else:
                cookies_dict = raw_cookies

            # 2. Налаштовуємо сесію
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": self.base_url,
                "Referer": schedule_url,
            }
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            session = AsyncSession(
                timeout=20.0,
                headers=headers,
                cookies=cookies_dict,
                impersonate="chrome110"
            )

            # 3. Використовуємо сесію в DtekClient
            async with DtekClient(
                self.site_key,
                ajax_url=f"{self.base_url}/ua/ajax",
                session=session
            ) as client:
                group_info = await client.get_group_by_address(
                    city=self.city,
                    street=self.street,
                    house_number=self.house
                )

                schedule = await client.get_today_schedule(
                    city=self.city,
                    street=self.street,
                    house_number=self.house
                )

                return {
                    "group": group_info,
                    "schedule": schedule
                }

        except DtekClientError as err:
            raise UpdateFailed(f"Помилка оновлення даних DTEK: {err}")
        except Exception as err:
            raise UpdateFailed(f"Непередбачена помилка: {err}")