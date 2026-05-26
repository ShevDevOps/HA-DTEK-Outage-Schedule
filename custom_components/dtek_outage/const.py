from datetime import timedelta

DOMAIN = "dtek_outage"
UPDATE_INTERVAL = timedelta(minutes=15)

CONF_SITE_KEY = "site_key"
CONF_CITY = "city"
CONF_STREET = "street"
CONF_HOUSE = "house"

SITE_URLS = {
    "krem": "https://www.dtek-krem.com.ua",
    "kem": "https://www.dtek-kem.com.ua",
    "oem": "https://www.dtek-oem.com.ua",
}
