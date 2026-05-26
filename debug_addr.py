import asyncio
import logging
from custom_components.dtek_outage.api_client.client import DtekClient
from custom_components.dtek_outage.api_client.browser_auth import get_cleared_cookies
from curl_cffi.requests import AsyncSession

# Налаштуємо логування, щоб бачити прогрес Playwright
logging.basicConfig(level=logging.INFO)

async def debug_address():
    url = "https://www.dtek-kem.com.ua/ua/shutdowns"
    
    print(f"--- Крок 1: Обхід WAF через Playwright для {url} ---")
    try:
        # Отримуємо куки та токен через реальний браузер
        cookies, csrf_token = await get_cleared_cookies(url)
        print(f"Отримано CSRF токен: {csrf_token}")
    except Exception as e:
        print(f"Не вдалося пройти WAF: {e}")
        return

    # 2. Створюємо сесію з отриманими даними
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRF-Token": csrf_token,
        "Referer": url,
    }

    async with AsyncSession(
        impersonate="chrome110",
        headers=headers,
        cookies=cookies
    ) as session:
        
        async with DtekClient(
            "kem", 
            ajax_url="https://www.dtek-kem.com.ua/ua/ajax",
            session=session
        ) as client:
            print("--- Крок 2: Пошук вулиці через API з куками ---")
            try:
                streets = await client.get_streets("м. Київ")
                
                search_term = "Екстер"
                matches = [s.name for s in streets if search_term.lower() in s.name.lower()]
                
                if not matches:
                    print(f"Вулиць з '{search_term}' не знайдено.")
                    print(f"Приклад назв: {[s.name for s in streets[:10]]}")
                else:
                    for m in matches:
                        print(f"Знайдено точну назву для конфігурації: '{m}'")
                        
                        # Відразу перевіримо номери будинків для цієї вулиці
                        res = await client.get_home_num("м. Київ", m)
                        print(f"Доступні номери будинків (перші 10): {list(res.houses.keys())[:10]}")
                        
            except Exception as e:
                print(f"Помилка під час запиту до API: {e}")

if __name__ == "__main__":
    asyncio.run(debug_address())