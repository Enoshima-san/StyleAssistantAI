SEARCH_QUERY = "майка женская"


# --- Параметры для парсера ---
# Количество одновременных запросов для получения характеристик товара
MAX_CONCURRENT_REQUESTS = 25

# Задержка между запросами (в секундах). Рекомендуется 0 или очень маленькое значение,
# если используется MAX_CONCURRENT_REQUESTS, так как Semaphore уже регулирует нагрузку.
REQUEST_DELAY = 0.05

# --- Заголовки для запросов ---
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.wildberries.ru/",
    "Origin": "https://www.wildberries.ru",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
}


# --- Параметры для сохранения ---
JSON_OUTPUT_FILE = "Результат парсинга.json"

# --- Параметры поиска ---
# Количество страниц для парсинга
SEARCH_PAGES = "ALL"        # Если ввести "ALL" то парсятся все страницы


# --- Автоматизация ---
# Автоматический запуск парсера
AUTO_RUN = False               # True - включить автоматизацию, False - выключить
RUN_INTERVAL_MINUTES = 1     # Интервал между запусками в минутах
MAX_RUNS = None               # Максимальное количество запусков (None - бесконечно)


# --- API URLs (на всякий случай, если понадобится изменить) ---
# (Можно оставить как константы, если не планируется часто менять)
SEARCH_URL_TEMPLATE = "https://search.wb.ru/exactmatch/ru/common/v13/search?ab_testing=false&appType=1&curr=rub&dest=-1257786&hide_dtype=13&lang=ru&page={page}&query={keyword}&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false"
# Остальные URL формируются динамически в коде парсера