# tests/test_sensor.py
from unittest.mock import AsyncMock, patch, Mock
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.const import STATE_UNKNOWN

from custom_components.dtek_outage.const import DOMAIN

# Фікстура для конфігурації
@pytest.fixture
def mock_config():
    return {
        DOMAIN: {
            "site_key": "kem",
            "city": "м. Київ",
            "street": "вул. Хрещатик",
            "house": "1"
        }
    }

@pytest.mark.asyncio
async def test_sensors_creation_and_attributes(hass: HomeAssistant, mock_config):
    """Тестування створення сенсорів та їх атрибутів за допомогою Mock-об'єкта API."""
    
    # Створюємо правильний мок для статусу (де .name — це рядок)
    mock_status = Mock()
    mock_status.name = "YES"
    mock_status.has_outage = False

    # Імітуємо повернення даних від бібліотеки
    mock_data = {
        "group": AsyncMock(group_id="GPV3", group_display_name="Черга 3", city="м. Київ", street="вул. Хрещатик"),
        "schedule": {"00:00-00:30": mock_status}
    }
    # Підміняємо метод _async_update_data у координаторі, щоб не робити реальні HTTP-запити
    with patch(
        "custom_components.dtek_outage.coordinator.DtekUpdateCoordinator._async_update_data",
        return_value=mock_data
    ):
        # Запускаємо інтеграцію
        assert await async_setup_component(hass, DOMAIN, mock_config)
        await hass.async_block_till_done()

        # 1. Перевіряємо сенсор групи (Черги)
        group_sensor_id = "sensor.cherga_vidkliuchen_1" # Зверніть увагу на slugify імені
        group_state = hass.states.get(group_sensor_id)
        
        assert group_state is not None
        assert group_state.state == "Черга 3"
        assert group_state.attributes.get("group_id") == "GPV3"

        # 2. Перевіряємо сенсор розкладу
        schedule_sensor_id = "sensor.grafik_vidkliuchen_1"
        schedule_state = hass.states.get(schedule_sensor_id)
        
        assert schedule_state is not None
        assert schedule_state.state == "Оновлено"
        # Перевіряємо, що тайм-слоти успішно додалися як атрибути
        assert schedule_state.attributes.get("00:00-00:30") == "YES"
