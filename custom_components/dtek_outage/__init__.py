import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_SITE_KEY, CONF_CITY, CONF_STREET, CONF_HOUSE
from .coordinator import DtekUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Платформи, які підтримує ваша інтеграція (у вашому випадку — сенсори)
PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Налаштування інтеграції DTEK через Config Flow entry."""
    hass.data.setdefault(DOMAIN, {})

    # Отримуємо конфігурацію, яку користувач ввів через інтерфейс
    conf = entry.data

    # Створюємо координатор для цього запису
    coordinator = DtekUpdateCoordinator(
        hass,
        site_key=conf.get(CONF_SITE_KEY),
        city=conf.get(CONF_CITY),
        street=conf.get(CONF_STREET),
        house=conf.get(CONF_HOUSE)
    )

    # Запускаємо перше отримання даних перед реєстрацією платформ
    await coordinator.async_config_entry_first_refresh()

    # Зберігаємо дані в hass.data, щоб sensor.py мав до них доступ за entry_id
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": conf,
    }

    # Реєструємо пов'язані платформи (викличе async_setup_entry у sensor.py)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Реєструємо слухач для оновлення параметрів (якщо користувач змінить щось через Опції)
    # entry.async_on_unload(entry.add_to_updates_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Видалення або перезапуск інтеграції з інтерфейсу."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Очищаємо пам'ять, виділену під цей entry_id
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Перезавантаження конфігураційного запису при оновленні налаштувань."""
    await hass.config_entries.async_reload(entry.entry_id)