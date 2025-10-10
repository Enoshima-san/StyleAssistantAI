import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor, as_completed
from functions import collect_product_info
from config import *


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('incremental_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.set_script_timeout(30)
    return driver


def get_current_products_links(driver, item_name=SEARCH_QUERY, max_products=MAX_PRODUCTS):
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

        # Скроллинг
        logger.info("📜 Загружаем список товаров...")
        products_urls = set()
        last_count = 0
        no_new_products_count = 0
        max_scroll_attempts = 50 if max_products == "ALL" else 20  # Больше попыток для "ALL"

        for attempt in range(max_scroll_attempts):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

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
        return products_urls

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при сборе ссылок: {e}")
        return []

def load_existing_data():
    try:
        with open('PRODUCTS_DATA.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.warning("⚠️ Файл PRODUCTS_DATA.json не найден. Будет создан новый.")
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки существующих данных: {e}")
        return []

def save_data(data):
    try:
        with open('PRODUCTS_DATA.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        logger.info(f"💾 Данные сохранены в PRODUCTS_DATA.json ({len(data)} товаров)")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения данных: {e}")

def find_new_products(current_urls, existing_data):
    # Поиск новых товаров, которых нет в существующих данных
    existing_urls = {product.get('product_url') for product in existing_data}
    new_urls = [url for url in current_urls if url not in existing_urls]
    
    logger.info(f"📊 Статистика:")
    logger.info(f"   📥 Текущие товары: {len(current_urls)}")
    logger.info(f"   💾 Существующие товары: {len(existing_data)}")
    logger.info(f"   🆕 Новые товары: {len(new_urls)}")
    
    return new_urls

def parse_new_products(urls, max_workers=MAX_WORKERS):
    # Парсинг новых товаров (аналогично функции из main.py)
    if not urls:
        return []

    logger.info(f"🚀 Запуск парсинга {len(urls)} новых товаров в {max_workers} потоках")

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
                time.sleep(RETRY_DELAY)

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

    results = []
    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(worker, url): url for url in urls}

            for i, future in enumerate(as_completed(future_to_url)):
                url = future_to_url[future]
                try:
                    result = future.result(timeout=TASK_TIMEOUT)
                    results.append(result)

                    name = result.get('product_name', 'Unknown')[:40]
                    price = result.get('product_ozon_card_price', 'No price')
                    material = result.get('material', 'N/A')
                    image_status = "🖼️" if result.get('product_image_url', 'Нет данных') not in ['Нет данных', 'Ошибка загрузки изображения'] else "❌"

                    if price != 'Нет данных' and result.get('product_name') != 'Ошибка загрузки':
                        status = "✅"
                    else:
                        status = "❌"

                    logger.info(f"{status}{image_status} Новый товар {i + 1}/{len(urls)} - {name}... - {price}")

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

        # Статистика
        total_time = time.time() - start_time
        successful = len([p for p in results if p.get('product_ozon_card_price') != 'Нет данных'])
        failed = len(results) - successful

        logger.info(f"📊 Статистика парсинга новых товаров:")
        logger.info(f"   ✅ Успешно: {successful}")
        logger.info(f"   ❌ Неудачно: {failed}")
        logger.info(f"   📊 Эффективность: {(successful / len(results) * 100):.1f}%")
        logger.info(f"   ⏱️ Время: {total_time:.2f} сек")

    except Exception as e:
        logger.error(f"❌ Ошибка в пуле потоков: {e}")

    return results

def incremental_parse(min_new_products=1):
    """
    Основная функция инкрементального парсинга
    
    Args:
        min_new_products (int): Минимальное количество новых товаров для запуска парсинга
    """
    logger.info("🔄 Запуск инкрементального парсера Ozon")
    
    start_time = time.time()
    driver = None
    
    try:
        # Загрузка существующих данных
        existing_data = load_existing_data()
        logger.info(f"💾 Загружено {len(existing_data)} существующих товаров")
        
        # Сбор текущих ссылок
        logger.info("📥 Сбор текущих ссылок на товары...")
        driver = setup_driver(headless=True)
        current_urls = get_current_products_links(driver, item_name=SEARCH_QUERY, max_products=MAX_PRODUCTS)
        
        if not current_urls:
            logger.error("❌ Не удалось собрать текущие ссылки на товары")
            return False
        
        # Поиск новых товаров
        new_urls = find_new_products(current_urls, existing_data)
        
        if len(new_urls) < min_new_products:
            logger.info(f"ℹ️ Новых товаров ({len(new_urls)}) меньше минимального порога ({min_new_products}). Парсинг не требуется.")
            return False
        
        logger.info(f"🎯 Найдено {len(new_urls)} новых товаров для парсинга")
        
        # Закрываем драйвер сбора ссылок
        driver.quit()
        driver = None
        
        # Парсинг новых товаров
        new_products_data = parse_new_products(new_urls, max_workers=MAX_WORKERS)
        
        if new_products_data:
            # Объединение старых и новых данных
            all_data = existing_data + new_products_data
            
            # Сохранение объединенных данных
            save_data(all_data)
            
            # Детальная статистика
            successful_new = len([p for p in new_products_data if p.get('product_ozon_card_price') != 'Нет данных'])
            
            logger.info("🎉 === ИНКРЕМЕНТАЛЬНЫЙ ПАРСИНГ ЗАВЕРШЕН ===")
            logger.info(f"📥 Всего товаров в базе: {len(all_data)}")
            logger.info(f"🆕 Новых товаров добавлено: {len(new_products_data)}")
            logger.info(f"✅ Успешно новых: {successful_new}")
            logger.info(f"❌ Неудачно новых: {len(new_products_data) - successful_new}")
            
            # Вывод информации о новых товарах
            if successful_new > 0:
                logger.info("🆕 === НОВЫЕ ТОВАРЫ ===")
                successful_products = [p for p in new_products_data if p.get('product_ozon_card_price') != 'Нет данных']
                for i, product in enumerate(successful_products):
                    name = product.get('product_name', 'N/A')[:50]
                    ozon_price = product.get('product_ozon_card_price', 'N/A')
                    material = product.get('material', 'N/A')
                    logger.info(f"{i + 1}. {name} - {ozon_price} (Материал: {material})")
            
            return True
        else:
            logger.error("❌ Не удалось получить данные о новых товарах")
            return False
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в инкрементальном парсере: {e}")
        return False
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
        total_time = time.time() - start_time
        logger.info(f"⏱️ Общее время выполнения: {total_time:.2f} секунд")

if __name__ == '__main__':
    # Можно настроить минимальное количество новых товаров для запуска парсинга
    # incremental_parse(min_new_products=5)  # Запустит парсинг только если найдено минимум 5 новых товаров
    incremental_parse(min_new_products=1)  # Запустит парсинг при любом количестве новых товаров