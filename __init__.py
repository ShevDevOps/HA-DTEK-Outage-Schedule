import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery

from .const import DOMAIN, CONF_SITE_KEY, CONF_CITY, CONF_STREET, CONF_HOUSE
from .coordinator import DtekUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_SITE_KEY): cv.string,
        vol.Required(CONF_CITY): cv.string,
        vol.Required(CONF_STREET): cv.string,
        vol.Required(CONF_HOUSE): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Налаштування інтеграції через configuration.yaml."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    coordinator = DtekUpdateCoordinator(
        hass,
        site_key=conf[CONF_SITE_KEY],
        city=conf[CONF_CITY],
        street=conf[CONF_STREET],
        house=conf[CONF_HOUSE]
    )

    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinator"] = coordinator
    hass.data[DOMAIN]["config"] = conf

    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    return True
