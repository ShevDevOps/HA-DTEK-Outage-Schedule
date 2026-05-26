import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import re
import logging

from .const import DOMAIN, SITE_URLS
from .api_client.client import DtekClient
from .api_client.browser_auth import get_cleared_cookies
from curl_cffi.requests import AsyncSession

_LOGGER = logging.getLogger(__name__)

# Допоміжна функція для створення сесії (аналог вашої з test.py)
async def _create_setup_session(base_url: str) -> AsyncSession:
    schedule_url = f"{base_url}/ua/shutdowns"
    cookies, csrf_token = await get_cleared_cookies(schedule_url)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": base_url,
        "Referer": schedule_url,
    }
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token
        
    return AsyncSession(timeout=15.0, headers=headers, cookies=cookies, impersonate="chrome110")


class DtekConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Майстер налаштування DTEK."""
    
    VERSION = 1

    def __init__(self):
        self.user_data = {}
        self._streets = []
        self._houses = []

    async def async_step_user(self, user_input=None):
        """Крок 1: Вибір регіону та введення міста."""
        errors = {}
        
        if user_input is not None:
            self.user_data.update(user_input)
            base_url = SITE_URLS.get(self.user_data["site_key"])
            
            try:
                # Робимо запит для отримання списку вулиць
                session = await _create_setup_session(base_url)
                async with DtekClient(self.user_data["site_key"], ajax_url=f"{base_url}/ua/ajax", session=session) as client:
                    streets_obj = await client.get_streets(self.user_data["city"])
                    if not streets_obj:
                        errors["base"] = "city_not_found"
                    else:
                        self._streets = [s.name for s in streets_obj]
                        return await self.async_step_street()
            except Exception as e:
                _LOGGER.error("Помилка отримання вулиць: %s", e)
                errors["base"] = "connection_error"

        # Схема форми для першого кроку
        schema = vol.Schema({
            vol.Required("site_key", default="kem"): vol.In({
                "kem": "Київські електромережі",
                "krem": "Київські регіональні (Область)",
                "oem": "Одеські електромережі"
            }),
            vol.Required("city", default="м. Київ"): str,
        })
        
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_street(self, user_input=None):
        """Крок 2: Вибір вулиці з випадаючого списку з фільтрацією."""
        errors = {}
        
        if user_input is not None:
            self.user_data.update(user_input)
            base_url = SITE_URLS.get(self.user_data["site_key"])
            
            try:
                # Отримуємо номери будинків для обраної вулиці
                session = await _create_setup_session(base_url)
                async with DtekClient(self.user_data["site_key"], ajax_url=f"{base_url}/ua/ajax", session=session) as client:
                    response = await client.get_home_num(self.user_data["city"], self.user_data["street"])
                    
                    # Сортуємо будинки як рядки (або числа), щоб вони йшли по порядку
                    self._houses = sorted(list(response.houses.keys()), key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x)])
                    return await self.async_step_house()
            except Exception as e:
                _LOGGER.error("Помилка отримання будинків: %s", e)
                errors["base"] = "connection_error"

        # Використовуємо рядок "dropdown" замість SelectWidgetMode.DROPDOWN
        street_schema = vol.Schema({
            vol.Required("street"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=self._streets,
                    mode="dropdown",
                    sort=True
                )
            )
        })

        return self.async_show_form(
            step_id="street",
            data_schema=street_schema,
            errors=errors
        )

    async def async_step_house(self, user_input=None):
        """Крок 3: Вибір будинку з фільтрацією (замість радіобаттонів)."""
        if user_input is not None:
            self.user_data.update(user_input)
            
            # Створюємо запис в Home Assistant
            title = f"{self.user_data['city']}, {self.user_data['street']}, {self.user_data['house']}"
            return self.async_create_entry(title=title, data=self.user_data)

        # Перетворюємо вибір будинку теж на Dropdown з пошуком через рядок "dropdown"
        house_schema = vol.Schema({
            vol.Required("house"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=self._houses,
                    mode="dropdown",
                    sort=False
                )
            )
        })
    
        return self.async_show_form(
            step_id="house",
            data_schema=house_schema
        )