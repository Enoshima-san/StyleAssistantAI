import time
import schedule
import logging
import threading
from datetime import datetime
from incremental_parser import incremental_parse
from main import main as full_parse
from config import *


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AdvancedScheduler:
    def __init__(self):
        self.is_running = False
        self.last_incremental_run = None
        self.last_full_run = None

    def run_incremental_parse(self):
        def incremental_worker():
            try:
                logger.info("🔄 Запуск инкрементального парсинга...")
                self.last_incremental_run = datetime.now()
                success = incremental_parse(min_new_products=1)
                if success:
                    logger.info("✅ Инкрементальный парсинг завершен успешно")
                else:
                    logger.info("ℹ️ Инкрементальный парсинг не нашел новых товаров")
            except Exception as e:
                logger.error(f"❌ Ошибка в инкрементальном парсинге: {e}")

        thread = threading.Thread(target=incremental_worker)
        thread.daemon = True
        thread.start()

    def run_full_parse(self):
        #Запуск полного парсинга в отдельном потоке
        def full_worker():
            try:
                logger.info("🎯 Запуск ПОЛНОГО парсинга...")
                self.last_full_run = datetime.now()
                full_parse()
                logger.info("✅ Полный парсинг завершен")
            except Exception as e:
                logger.error(f"❌ Ошибка в полном парсинге: {e}")

        thread = threading.Thread(target=full_worker)
        thread.daemon = True
        thread.start()

    def print_status(self):
        status = []
        status.append("=== СТАТУС ПЛАНИРОВЩИКА ===")
        status.append(f"🕒 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if self.last_incremental_run:
            status.append(f"🔄 Последний инкрементальный: {self.last_incremental_run.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            status.append("🔄 Инкрементальный: еще не запускался")

        if self.last_full_run:
            status.append(f"🎯 Последний полный: {self.last_full_run.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            status.append("🎯 Полный: еще не запускался")

        status.append("📅 Расписание:")
        status.append(f"   - Инкрементальный: каждые {INCREMENTAL_INTERVAL_MINUTES} часов")
        status.append(f"   - Полный: каждые {FULL_INTERVAL_HOURS} часов")
        status.append("===========================")

        for line in status:
            logger.info(line)

    def setup_schedule(self):
        # Инкрементальный парсинг
        schedule.every(INCREMENTAL_INTERVAL_MINUTES).minutes.do(self.run_incremental_parse)
        # Полный парсинг каждые 24 часа
        schedule.every(FULL_INTERVAL_HOURS).hours.do(self.run_full_parse)
        # Статус каждый n минут
        schedule.every(INCREMENTAL_INTERVAL_MINUTES).minutes.do(self.print_status)

    def start(self):
        logger.info("🚀 Запуск расширенного планировщика парсинга")
        self.is_running = True
        self.setup_schedule()

        # Первый запуск инкрементального парсинга сразу
        logger.info("⏰ Первый запуск инкрементального парсинга...")
        self.run_incremental_parse()
        time.sleep(10)

        self.print_status()
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Проверка каждую минуту
        except KeyboardInterrupt:
            logger.info("🛑 Планировщик остановлен пользователем")
            self.is_running = False

    def stop(self):
        self.is_running = False


def main():
    scheduler = AdvancedScheduler()
    print("=== УПРАВЛЕНИЕ ПЛАНИРОВЩИКОМ ===")
    print("1 - Запуск планировщика")
    print("2 - Однократный инкрементальный парсинг")
    print("3 - Однократный полный парсинг")
    print("4 - Статус")
    print("0 - Выход")
    while True:
        choice = input("\nВыберите действие (0-4): ").strip()

        if choice == "1":
            print("Запуск планировщика...")
            scheduler.start()
            break
        elif choice == "2":
            print("Запуск инкрементального парсинга...")
            scheduler.run_incremental_parse()
        elif choice == "3":
            print("Запуск полного парсинга...")
            scheduler.run_full_parse()
        elif choice == "4":
            scheduler.print_status()
        elif choice == "0":
            print("Выход...")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == '__main__':
    main()