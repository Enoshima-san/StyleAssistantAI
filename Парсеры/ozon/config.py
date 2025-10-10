# Поисковый запрос
SEARCH_QUERY = "штаны черные"

# Максимальное количество товаров для парсинга
MAX_PRODUCTS = 30 # при значении "ALL" парсятся все товары

# Максимальное количество потоков для парсинга
MAX_WORKERS = 10

# Таймауты (в секундах)
PAGE_LOAD_TIMEOUT = 15
ELEMENT_TIMEOUT = 8
SCROLL_DELAY = 1

# Настройки повторных попыток
MAX_RETRIES = 3  # Количество повторных попыток при ошибках
RETRY_DELAY = 3  # Задержка между попытками в секундах
TASK_TIMEOUT = 15  # Таймаут на выполнение одной задачи

# Настройки обхода защиты
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

INCREMENTAL_INTERVAL_MINUTES = 90  # Интервал инкрементального парсинга в минутах
FULL_INTERVAL_HOURS = 24        # Интервал полного парсинга в часах