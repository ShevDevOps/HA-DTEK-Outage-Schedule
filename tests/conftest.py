import sys
import os
import pytest

# 1. Додаємо шлях до папки config-test
config_test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if config_test_dir not in sys.path:
    sys.path.insert(0, config_test_dir)

# 2. Активуємо плагін з фікстурами Home Assistant
pytest_plugins = "pytest_homeassistant_custom_component"

# 3. Дозволяємо Home Assistant завантажувати custom_components під час тестів
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
