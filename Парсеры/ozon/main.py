import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from functions import page_down, collect_product_info
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_settings():
    logger.info("=== НАСТРОЙКИ ПАРСЕРА ===")
    logger.info(f"Поисковый запрос: {SEARCH_QUERY}")

    if MAX_PRODUCTS == "ALL":
        logger.info(f"Максимум товаров: ВСЕ товары (без ограничений)")
    else:
        logger.info(f"Максимум товаров: {MAX_PRODUCTS}")

    logger.info(f"Количество потоков: {MAX_WORKERS}")
    logger.info(f"Таймаут загрузки: {PAGE_LOAD_TIMEOUT} сек")
    logger.info("=========================")


def setup_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--dns-prefetch-disable')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--enable-javascript')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.set_script_timeout(30)
    return driver


def get_products_links(driver, item_name=SEARCH_QUERY, max_products=MAX_PRODUCTS):
    try:
        logger.info(f"🔍 Начинаем поиск товаров: '{item_name}'")
        driver.get('https://ozon.ru')
        time.sleep(3)
        try:
            find_input = WebDriverWait(driver, ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.NAME, 'text'))
            )
            find_input.clear()
            find_input.send_keys(item_name)
            time.sleep(1)
            find_input.send_keys(Keys.ENTER)
            time.sleep(3)
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return []


        # Скроллинг для загрузки товаров
        logger.info("📜 Загружаем список товаров...")
        products_urls = set()
        last_count = 0
        no_new_products_count = 0
        max_scroll_attempts = 50 if max_products == "ALL" else 20  # Больше попыток для "ALL"

        for attempt in range(max_scroll_attempts):
            # Скроллинг
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Ждем загрузки

            # Сбор ссылок после каждого скролла
            try:
                links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"]')
                current_count = len(products_urls)

                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if href and '/product/' in href:
                            clean_url = href.split('?')[0].split('#')[0]
                            if '/product/' in clean_url and len(clean_url) > 30:
                                products_urls.add(clean_url)
                    except Exception:
                        continue

                # Проверяем, появились ли новые товары
                new_count = len(products_urls)
                if new_count == current_count:
                    no_new_products_count += 1
                else:
                    no_new_products_count = 0
                    logger.info(f"📎 Найдено товаров: {new_count}")

                # Если не появилось новых товаров - останавливаемся
                if no_new_products_count >= 10:
                    logger.info("🚫 Новые товары перестали подгружаться, завершаем скроллинг")
                    break

                # Если не "ALL" и достигли лимита - останавливаемся
                if max_products != "ALL" and new_count >= max_products:
                    logger.info(f"🎯 Достигнут лимит в {max_products} товаров")
                    break

            except Exception as e:
                logger.warning(f"⚠️ Ошибка при сборе ссылок после скролла: {e}")
                continue

        # Применяем ограничение только если не "ALL"
        products_urls = list(products_urls)
        if max_products != "ALL" and max_products > 0:
            products_urls = products_urls[:max_products]

        logger.info(f"✅ ИТОГО найдено товаров: {len(products_urls)}")

        # Сохранение ссылок
        if products_urls:
            with open('products_urls_dict.json', 'w', encoding='utf-8') as file:
                json.dump({k: v for k, v in enumerate(products_urls)}, file, indent=4, ensure_ascii=False)

        return products_urls

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при сборе ссылок: {e}")
        return []


def parse_products_parallel(urls, max_workers=MAX_WORKERS):
    if not urls:
        return []

    logger.info(f"🚀 Запуск парсинга {len(urls)} товаров в {max_workers} потоках")

    def worker(url):
        driver = None
        for retry_count in range(MAX_RETRIES + 1):
            try:
                driver = setup_driver(headless=True)

                time.sleep(2)

                result = collect_product_info(driver, url)


                if (result.get('product_ozon_card_price') != 'Нет данных' or
                        result.get('product_name') != 'Не удалось получить название'):
                    return result
                else:
                    logger.warning(f"⚠️ Неудачная попытка {retry_count + 1}/{MAX_RETRIES + 1} для {url}")

            except TimeoutException as e:
                logger.warning(f"⚠️ Таймаут при парсинге {url} (попытка {retry_count + 1}/{MAX_RETRIES + 1}): {e}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при парсинге {url} (попытка {retry_count + 1}/{MAX_RETRIES + 1}): {e}")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass

            if retry_count < MAX_RETRIES:
                time.sleep(3)

        # Если все попытки неудачны, возвращаем результат с ошибкой
        logger.error(f"❌ Превышено количество попыток для {url}")
        return {
            'product_url': url,
            'error': f'Failed after {MAX_RETRIES + 1} attempts',
            'product_name': 'Ошибка загрузки',
            'product_ozon_card_price': 'Нет данных',
            'product_regular_price': 'Нет данных',
            'product_image_url': 'Нет данных',
            'material': 'Не указано',
            'material_composition': 'Не указано',
            'lining_material': 'Не указано',
            'color': 'Не указано',
            'type': 'Не указано'
        }

    # Запуск в пуле потоков
    results = []
    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(worker, url): url for url in urls}

            for i, future in enumerate(as_completed(future_to_url)):
                url = future_to_url[future]
                try:
                    result = future.result(timeout=90)
                    results.append(result)

                    name = result.get('product_name', 'Unknown')[:40]
                    price = result.get('product_ozon_card_price', 'No price')
                    material = result.get('material', 'N/A')
                    image_status = "🖼️" if result.get('product_image_url', 'Нет данных') not in ['Нет данных','Ошибка загрузки изображения'] else "❌"

                    if price != 'Нет данных' and result.get('product_name') != 'Ошибка загрузки':
                        status = "✅"
                    else:
                        status = "❌"

                    logger.info(f"{status}{image_status} Прогресс: {i + 1}/{len(urls)} - {name}... - {price}")

                    if material != 'Не указано':
                        logger.info(f"   🧵 Материал: {material}")

                except TimeoutException:
                    logger.error(f"⏰ Таймаут выполнения для {url}")
                    results.append({
                        'product_url': url,
                        'error': 'Task execution timeout',
                        'product_name': 'Таймаут выполнения',
                        'product_ozon_card_price': 'Нет данных',
                        'product_regular_price': 'Нет данных',
                        'product_image_url': 'Нет данных',
                        'material': 'Не указано',
                        'material_composition': 'Не указано',
                        'lining_material': 'Не указано',
                        'color': 'Не указано',
                        'type': 'Не указано'
                    })
                except Exception as e:
                    logger.error(f"❌ Ошибка получения результата для {url}: {e}")
                    results.append({
                        'product_url': url,
                        'error': str(e),
                        'product_name': 'Ошибка выполнения',
                        'product_ozon_card_price': 'Нет данных',
                        'product_regular_price': 'Нет данных',
                        'product_image_url': 'Нет данных',
                        'material': 'Не указано',
                        'material_composition': 'Не указано',
                        'lining_material': 'Не указано',
                        'color': 'Не указано',
                        'type': 'Не указано'
                    })

        # Статистика скорости
        total_time = time.time() - start_time
        speed = len(urls) / total_time if total_time > 0 else 0

        # Подсчет успешных и неудачных парсингов
        successful = len([p for p in results if p.get('product_ozon_card_price') != 'Нет данных'])
        failed = len(results) - successful

        logger.info(f"📊 Статистика парсинга:")
        logger.info(f"   ✅ Успешно: {successful}")
        logger.info(f"   ❌ Неудачно: {failed}")
        logger.info(f"   📊 Эффективность: {(successful / len(results) * 100):.1f}%")
        logger.info(f"   ⏱️ Общее время: {total_time:.2f} сек")
        logger.info(f"   🚀 Средняя скорость: {speed:.2f} товаров/сек")

    except Exception as e:
        logger.error(f"❌ Ошибка в пуле потоков: {e}")

    return results


def main():
    logger.info("🎯 Запуск парсера Ozon")
    print_settings()

    start_time = time.time()
    driver = None

    try:
        logger.info("📥 ЭТАП 1: Сбор ссылок на товары...")
        driver = setup_driver(headless=False)
        urls = get_products_links(driver, item_name=SEARCH_QUERY, max_products=MAX_PRODUCTS)

        if not urls:
            logger.error("❌ Не удалось собрать ссылки на товары")
            return []

        # Закрываем драйвер сбора ссылок
        driver.quit()
        driver = None

        logger.info("🛒 ЭТАП 2: Начинаем многопоточный парсинг товаров...")
        products_data = parse_products_parallel(urls, max_workers=MAX_WORKERS)

        # Сохранение результатов
        if products_data:
            with open('PRODUCTS_DATA.json', 'w', encoding='utf-8') as file:
                json.dump(products_data, file, indent=4, ensure_ascii=False)

            # Статистика
            successful = len([p for p in products_data if p.get('product_ozon_card_price') != 'Нет данных'])
            failed = len(products_data) - successful
            images_found = len([p for p in products_data if
                                p.get('product_image_url') not in ['Нет данных', 'Ошибка загрузки изображения',
                                                                   'Изображение не найдено']])
            materials_found = len([p for p in products_data if p.get('material') != 'Не указано'])

            logger.info("📈 === СТАТИСТИКА ===")
            logger.info(f"📥 Всего товаров: {len(products_data)}")
            logger.info(f"✅ Успешно: {successful} товаров")
            logger.info(f"❌ Не удалось: {failed} товаров")
            logger.info(f"🖼️ Изображений найдено: {images_found}")
            logger.info(f"🧵 Материалов найдено: {materials_found}")
            logger.info(f"📊 Эффективность: {(successful / len(products_data) * 100):.1f}%")

            # Вывод первых результатов
            if successful > 0:
                logger.info("🎁 === ПЕРВЫЕ РЕЗУЛЬТАТЫ ===")
                successful_products = [p for p in products_data if p.get('product_ozon_card_price') != 'Нет данных']
                for i, product in enumerate(successful_products[:3]):  # Показываем только 3 для наглядности
                    name = product.get('product_name', 'N/A')[:50]
                    ozon_price = product.get('product_ozon_card_price', 'N/A')
                    regular_price = product.get('product_regular_price', 'N/A')
                    material = product.get('material', 'N/A')
                    composition = product.get('material_composition', 'N/A')
                    lining = product.get('lining_material', 'N/A')
                    color = product.get('color', 'N/A')  # ДОБАВЛЕНО
                    type_ = product.get('type', 'N/A')  # ДОБАВЛЕНО
                    all_chars = product.get('all_characteristics', {})

                    logger.info(f"{i + 1}. {name}")
                    logger.info(f"   💳 Ozon Card: {ozon_price} | 💵 Обычная: {regular_price}")
                    logger.info(f"   🧵 Материал: {material}")
                    logger.info(f"   📊 Состав: {composition}")
                    logger.info(f"   🧵 Подкладка: {lining}")
                    logger.info(f"   🎨 Цвет: {color}")
                    logger.info(f"   📝 Тип: {type_}")
                    logger.info(f"   📋 ВСЕ ХАРАКТЕРИСТИКИ ({len(all_chars)}):")

                    # Выводим все характеристики
                    #for char_key, char_value in list(all_chars.items())[:10]:  # Первые 10 характеристик
                    #    logger.info(f"      • {char_key}: {char_value}")
                    #if len(all_chars) > 10:
                    #    logger.info(f"      ... и еще {len(all_chars) - 10} характеристик")

        return products_data

    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        return []

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

        total_time = time.time() - start_time
        logger.info(f"⏱️ Общее время выполнения: {total_time:.2f} секунд")
        logger.info("🏁 Работа парсера завершена")


if __name__ == '__main__':
    main()