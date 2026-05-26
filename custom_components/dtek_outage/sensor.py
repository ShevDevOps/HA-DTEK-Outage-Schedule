import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Налаштування сенсорів через Config Flow."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    conf = data["config"]
    
    async_add_entities([
        DtekGroupSensor(coordinator, conf),
        DtekScheduleSensor(coordinator, conf)
    ])


class DtekGroupSensor(CoordinatorEntity, SensorEntity):
    """Сенсор для відображення групи (черги) відключень."""

    def __init__(self, coordinator, conf):
        """Прив'язка до координатора."""
        super().__init__(coordinator)
        self._conf = conf

        # Генерація унікального ID
        address_id = f"{conf['site_key']}_{conf['city']}_{conf['street']}_{conf['house']}"
        self._attr_unique_id = f"dtek_group_{address_id}"
        self._attr_name = f"Черга відключень ({conf['house']})"
        self._attr_icon = "mdi:home-lightning-bolt-outline"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address_id)},
            name=f"DTEK {conf['city']}, {conf['street']}, {conf['house']}",
            manufacturer="DTEK",
            model="Blackout Schedule"
        )

    @property
    def native_value(self):
        """Повертає назву групи (наприклад, 'Черга планових відключень 3.1')."""
        if self.coordinator.data and "group" in self.coordinator.data and self.coordinator.data["group"]:
            return self.coordinator.data["group"].group_display_name
        return "Невідомо"

    @property
    def extra_state_attributes(self):
        """Додавання атрибутів до сенсорів."""
        attrs = {}
        if self.coordinator.data and "group" in self.coordinator.data and self.coordinator.data["group"]:
            group_data = self.coordinator.data["group"]
            attrs["group_id"] = group_data.group_id
            attrs["city"] = group_data.city
            attrs["street"] = group_data.street
        return attrs


class DtekScheduleSensor(CoordinatorEntity, SensorEntity):
    """Сенсор для відображення графіка відключень."""

    def __init__(self, coordinator, conf):
        """Прив'язка до координатора та збереження конфігу."""
        super().__init__(coordinator)
        self._conf = conf

        # Генерація унікального ID
        address_id = f"{conf['site_key']}_{conf['city']}_{conf['street']}_{conf['house']}"
        self._attr_unique_id = f"dtek_schedule_{address_id}"
        self._attr_name = f"Розклад відключень ({conf['house']})"
        self._attr_icon = "mdi:calendar-clock"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address_id)},
            name=f"DTEK {conf['city']}, {conf['street']}, {conf['house']}",
            manufacturer="DTEK",
            model="Blackout Schedule"
        )

    @property
    def native_value(self):
        """Базове значення сенсора."""
        if self.coordinator.data and "schedule" in self.coordinator.data and self.coordinator.data["schedule"]:
            return "Завантажено"
        return "Невідомо"

    @property
    def extra_state_attributes(self):
        """Розширені атрибути: передача структурованого розкладу на сьогодні/завтра."""
        attrs = {}
        
        # Безпечно витягуємо дані групи
        if self.coordinator.data and "group" in self.coordinator.data and self.coordinator.data["group"]:
            group_data = self.coordinator.data["group"]
            raw_group = str(group_data.group_id)
            clean_group = ''.join(filter(str.isdigit, raw_group)) or raw_group
            attrs["group_id"] = clean_group
            attrs["address"] = f"{group_data.city}, {group_data.street}, буд. {self._conf.get('house')}"

        # Захищена ініціалізація структури розкладу
        schedule_struct = {
            "today": {},
            "tomorrow": {}
        }

        if self.coordinator.data and "schedule" in self.coordinator.data and self.coordinator.data["schedule"]:
            raw_schedule = self.coordinator.data["schedule"]
            
            if isinstance(raw_schedule, dict):
                if "today" in raw_schedule or "tomorrow" in raw_schedule:
                    schedule_struct["today"] = raw_schedule.get("today") or {}
                    schedule_struct["tomorrow"] = raw_schedule.get("tomorrow") or {}
                else:
                    schedule_struct["today"] = raw_schedule
            elif hasattr(raw_schedule, "__dict__") or str(type(raw_schedule)).get("FactSchedule"):
                # На випадок якщо координатор повертає об'єкт Pydantic
                schedule_struct["today"] = getattr(raw_schedule, "today", {}) or {}
                schedule_struct["tomorrow"] = getattr(raw_schedule, "tomorrow", {}) or {}

        attrs["schedule"] = schedule_struct

        # Безпечна зворотна сумісність
        if isinstance(schedule_struct["today"], dict):
            for key, value in schedule_struct["today"].items():
                attrs[key] = value


        return attrs
