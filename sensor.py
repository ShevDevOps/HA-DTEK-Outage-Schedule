import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo


from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass: HomeAssistant,
                   config: ConfigType,
                   add_entities: AddEntitiesCallback,
                   discovery_info: DiscoveryInfoType | None = None):
    """Налаштування сенсорів DTEK."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    conf = hass.data[DOMAIN]["config"]
    add_entities([
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
        if self.coordinator.data and "group" in self.coordinator.data:
            return self.coordinator.data["group"].group_display_name
        return "Невідомо"

    @property
    def extra_state_attributes(self):
        """Додавання атрибутів до сенсорів."""
        attrs = {}
        if self.coordinator.data and "group" in self.coordinator.data:
            group_data = self.coordinator.data["group"]
            attrs["group_id"] = group_data.group_id
            attrs["city"] = group_data.city
            attrs["street"] = group_data.street
        return attrs



class DtekScheduleSensor(CoordinatorEntity, SensorEntity):
    """Сенсор для відображення поточного стану та розкладу."""

    def __init__(self, coordinator, conf):
        super().__init__(coordinator)
        self._conf = conf
        address_id = f"{conf['site_key']}_{conf['city']}_{conf['street']}_{conf['house']}"
        self._attr_unique_id = f"dtek_schedule_{address_id}"
        self._attr_name = f"Графік відключень ({conf['house']})"
        self._attr_icon = "mdi:calendar-clock"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address_id)}
        )

    @property
    def native_value(self):
        return "Оновлено"

    @property
    def extra_state_attributes(self):
        """Розширені атрибути: передача всього денного розкладу по слотах."""
        attrs = {}
        if self.coordinator.data and "schedule" in self.coordinator.data:
            schedule = self.coordinator.data["schedule"]
            if schedule:
                # Перетворюємо об'єкти SlotStatus у їх текстове представлення (YES, NO, MAYBE тощо)
                for time_slot, status in schedule.items():
                    attrs[time_slot] = status.name
        return attrs
