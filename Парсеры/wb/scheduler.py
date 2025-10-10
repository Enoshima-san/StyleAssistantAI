import schedule
import asyncio
import time
import datetime
import threading
from main import WildBerriesParser
import config


def calculate_next_run_time():
    """Вычисляет время следующего запуска"""
    now = datetime.datetime.now()
    next_run = now + datetime.timedelta(minutes=config.RUN_INTERVAL_MINUTES)
    return next_run


def print_time_until_next(next_run_time):
    """Выводит время до следующего парсинга"""
    now = datetime.datetime.now()
    time_until_next = next_run_time - now
    minutes_until = int(time_until_next.total_seconds() // 60)
    seconds_until = int(time_until_next.total_seconds() % 60)

    print(f"⏰ Следующий парсинг через: {minutes_until} минут {seconds_until} секунд")
    print(f"📅 Время следующего запуска: {next_run_time.strftime('%H:%M:%S')}")
    print("-" * 60)


def run_async_parsing():
    """Запуск асинхронного парсинга в отдельном потоке с новым event loop"""

    def run_in_thread():
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            current_time = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"🔄 [{current_time}] Запуск парсинга...")

            # Создаем новый парсер для каждого запуска
            wbp = WildBerriesParser()

            # Запускаем парсинг
            loop.run_until_complete(wbp.single_run())

            end_time = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"✅ [{end_time}] Парсинг завершен успешно")

            # Вычисляем и выводим время следующего запуска
            next_run = calculate_next_run_time()
            print_time_until_next(next_run)

        except Exception as e:
            error_time = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"❌ [{error_time}] Ошибка при парсинге: {e}")

            # Даже при ошибке показываем время следующего запуска
            next_run = calculate_next_run_time()
            print_time_until_next(next_run)
        finally:
            loop.close()

    thread = threading.Thread(target=run_in_thread)
    thread.daemon = True
    thread.start()


def start_scheduler():
    """Запуск планировщика"""
    print("📅 ПЛАНИРОВЩИК ПАРСЕРА ЗАПУЩЕН")
    print(f"⏰ Интервал парсинга: каждые {config.RUN_INTERVAL_MINUTES} минут")
    print(f"🔍 Поисковый запрос: '{config.SEARCH_QUERY}'")
    print("=" * 60)

    # Настройка расписания
    schedule.every(config.RUN_INTERVAL_MINUTES).minutes.do(run_async_parsing)

    # Первый запуск сразу
    print(f"🚀 [{datetime.datetime.now().strftime('%H:%M:%S')}] Первый запуск парсера...")
    run_async_parsing()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Планировщик остановлен")


if __name__ == "__main__":
    start_scheduler()