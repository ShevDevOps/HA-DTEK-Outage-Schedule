import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
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

    @property
    def native_value(self):
        """Повертає назву групи (наприклад, 'Черга планових відключень 3.1')."""
        if self.coordinator.data and "group" in self.coordinator.data:
            return self.coordinator.data["group"].group_display_name
        return "Невідомо"


class DtekScheduleSensor(CoordinatorEntity, SensorEntity):
    """Сенсор для відображення поточного стану та розкладу."""

    def __init__(self, coordinator, conf):
        super().__init__(coordinator)
        self._conf = conf
        address_id = f"{conf['site_key']}_{conf['city']}_{conf['street']}_{conf['house']}"
        self._attr_unique_id = f"dtek_schedule_{address_id}"
        self._attr_name = f"Графік відключень ({conf['house']})"
        self._attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self):
        return "Оновлено"
