# Використовуємо Debian як базу
FROM python:3.11-slim-bookworm

# Встановлюємо лише базові системні залежності для компіляції та налаштування часу
RUN apt-get update && apt-get install -y \
    wget \
    tzdata \
    libffi-dev \
    libssl-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Фіксуємо версії, щоб уникнути помилки AttributeError: module 'josepy' has no attribute 'ComparableX509'
# Також встановлюємо Home Assistant і ваші ліби
RUN pip install --no-cache-dir \
    josepy==1.13.0 \
    acme==2.6.0 \
    homeassistant==2024.1.5 \
    playwright==1.41.2 \
    curl_cffi==0.6.0b9 \
    pydantic

# Інсталюємо Chromium та його залежності (на Debian це відпрацює бездоганно)
RUN playwright install --with-deps chromium

# Вказуємо порт для Home Assistant
EXPOSE 8123

# Запуск Home Assistant
CMD ["hass", "-c", "/config"]