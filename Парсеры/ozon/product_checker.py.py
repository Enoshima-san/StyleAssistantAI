import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent.futures import ThreadPoolExecutor, as_completed
from functions import parse_ozon_prices, extract_price_from_text
from config import *


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('product_checker.log', encoding='utf-8'),
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
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.set_script_timeout(30)
    return driver


def load_articles_from_file(filename="Артикулы.txt"):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            articles = [line.strip() for line in file if line.strip()]

        logger.info(f"📥 Загружено {len(articles)} артикулов из файла {filename}")
        return articles
    except FileNotFoundError:
        logger.error(f"❌ Файл {filename} не найден")
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки артикулов: {e}")
        return []


def is_product_not_found(driver):
    try:
        # Проверка на страницу "Товар не найден"
        error_selectors = [
            'h1[contains(text(), "не найден")]',
            'h1[contains(text(), "Не найдено")]',
            'div[contains(text(), "404")]',
            'div[data-widget="webNotFound"]',
            '//*[contains(text(), "NotFound")]',
            '//*[contains(@class, "error404")]'
        ]
        product_not_found = False
        for selector in error_selectors:
            try:
                if selector.startswith('//'):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)

                if elements:
                    for element in elements:
                        if element.is_displayed():
                            product_not_found = True
                            break
                if product_not_found:
                    break
            except:
                continue
        # Дополнительная проверка по URL и заголовку
        current_url = driver.current_url.lower()
        page_title = driver.title.lower()

        if (product_not_found or
                "notfound" in current_url or
                "error" in current_url or
                "не найдено" in page_title or
                "not found" in page_title):
            return True

        return False
    except:
        return False


def is_product_available(driver):
    try:
        # Проверяем наличие основных элементов товара
        product_indicators = [
            'div[data-widget="webProductHeading"]',
            'h1[data-widget="webProductHeading"]',
            'div[data-widget="webPrice"]',
            'div[data-widget="webGallery"]',
            'button[data-widget="webAddToCart"]'
        ]

        for selector in product_indicators:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        return True
            except:
                continue

        return False
    except:
        return False


def get_product_prices(driver):
    #Получение цен товара через функцию из functions.py
    try:
        ozon_card_price, regular_price = parse_ozon_prices(driver)
        prices = {
            'ozon_card_price': 'Нет данных',
            'regular_price': 'Нет данных'
        }
        if ozon_card_price:
            prices['ozon_card_price'] = f"{ozon_card_price} ₽"
        if regular_price:
            prices['regular_price'] = f"{regular_price} ₽"

        # Если одна цена отсутствует, дублируем имеющуюся
        if prices['ozon_card_price'] == 'Нет данных' and prices['regular_price'] != 'Нет данных':
            prices['ozon_card_price'] = prices['regular_price']
        elif prices['regular_price'] == 'Нет данных' and prices['ozon_card_price'] != 'Нет данных':
            prices['regular_price'] = prices['ozon_card_price']
        return prices
    except Exception as e:
        logger.warning(f"⚠️ Ошибка получения цен: {e}")
        return {
            'ozon_card_price': 'Нет данных',
            'regular_price': 'Нет данных'
        }


def get_product_name(driver):
    try:
        name_selectors = [
            'div[data-widget="webProductHeading"] h1',
            'h1[data-widget="webProductHeading"]',
            'h1',
            '.a2k0'
        ]
        for selector in name_selectors:
            try:
                name_element = WebDriverWait(driver, ELEMENT_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                name = name_element.text.strip()
                if name and len(name) > 2:
                    return name
            except TimeoutException:
                continue

        # Альтернативный способ
        try:
            name_element = driver.find_element(By.TAG_NAME, 'h1')
            name = name_element.text.strip()
            if name and len(name) > 2:
                return name
        except:
            pass

        return "Не удалось получить название"
    except:
        return "Не удалось получить название"


def get_product_sizes(driver):
    sizes = []
    try:
        size_selectors = [
            'div[data-widget="webSizes"] button',
            'div[data-widget="webSizes"] div',
            'button[data-test-id="size-button"]',
            '.ui-a2',
            'div[class*="size"] button'
        ]

        for selector in size_selectors:
            try:
                size_elements = WebDriverWait(driver, ELEMENT_TIMEOUT).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                for size_element in size_elements:
                    try:
                        size_text = size_element.text.strip()
                        if size_text and len(size_text) < 10:
                            is_available = True
                            try:
                                class_attr = size_element.get_attribute('class') or ''
                                if 'disabled' in class_attr or 'unavailable' in class_attr or 'out-of-stock' in class_attr:
                                    is_available = False
                            except:
                                pass

                            sizes.append({
                                'size': size_text,
                                'available': is_available
                            })
                    except:
                        continue

                if sizes:
                    break
            except TimeoutException:
                continue
            except:
                continue
    except Exception as e:
        logger.warning(f"⚠️ Ошибка получения размеров: {e}")

    return sizes


def check_product_availability(driver, article):
    product_data = {
        'article': article,
        'available': False,
        'product_name': 'Не найден',
        'product_url': f'https://www.ozon.ru/product/{article}',
        'prices': {
            'ozon_card_price': 'Нет данных',
            'regular_price': 'Нет данных'
        },
        'sizes': [],
        'error': None
    }

    try:
        logger.info(f"🔍 Проверяем артикул: {article}")
        driver.get(product_data['product_url'])
        time.sleep(3)

        if is_product_not_found(driver):
            product_data['available'] = False
            product_data['product_name'] = 'Товар не найден'
            logger.info(f"❌ Товар {article} не найден")
            return product_data

        if not is_product_available(driver):
            product_data['available'] = False
            product_data['product_name'] = 'Товар недоступен'
            logger.info(f"❌ Товар {article} недоступен")
            return product_data

        product_data['available'] = True
        product_data['product_name'] = get_product_name(driver)
        product_data['prices'] = get_product_prices(driver)
        product_data['sizes'] = get_product_sizes(driver)

        # Логируем результат
        if product_data['available']:
            status_msg = f"✅ Товар {article} найден: {product_data['product_name'][:50]}..."
            if product_data['prices']['ozon_card_price'] != 'Нет данных':
                status_msg += f" | 💰 {product_data['prices']['ozon_card_price']}"
            if product_data['sizes']:
                available_sizes = [size['size'] for size in product_data['sizes'] if size['available']]
                if available_sizes:
                    status_msg += f" | 📏 {', '.join(available_sizes)}"
            logger.info(status_msg)

    except Exception as e:
        logger.error(f"❌ Ошибка при проверке артикула {article}: {e}")
        product_data['error'] = str(e)
        product_data['available'] = False

    return product_data


def check_products_parallel(articles, max_workers=MAX_WORKERS):
    if not articles:
        return []

    logger.info(f"🚀 Запуск проверки {len(articles)} артикулов в {max_workers} потоках")

    def worker(article):
        driver = None

        for retry_count in range(MAX_RETRIES + 1):
            try:
                driver = setup_driver(headless=True)
                time.sleep(2)  # Время на инициализацию
                result = check_product_availability(driver, article)
                return result

            except TimeoutException as e:
                logger.warning(f"⚠️ Таймаут при проверке {article} (попытка {retry_count + 1}/{MAX_RETRIES + 1}): {e}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при проверке {article} (попытка {retry_count + 1}/{MAX_RETRIES + 1}): {e}")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
            if retry_count < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        logger.error(f"❌ Превышено количество попыток для {article}")
        return {
            'article': article,
            'available': False,
            'product_name': 'Ошибка проверки',
            'product_url': f'https://www.ozon.ru/product/{article}',
            'prices': {
                'ozon_card_price': 'Нет данных',
                'regular_price': 'Нет данных'
            },
            'sizes': [],
            'error': f'Failed after {MAX_RETRIES + 1} attempts'
        }

    results = []
    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_article = {executor.submit(worker, article): article for article in articles}

            for i, future in enumerate(as_completed(future_to_article)):
                article = future_to_article[future]
                try:
                    result = future.result(timeout=TASK_TIMEOUT)
                    results.append(result)

                    # Логируем результат
                    name = result.get('product_name', 'Unknown')[:40]
                    available = result.get('available', False)
                    price = result.get('prices', {}).get('ozon_card_price', 'No price')

                    if available:
                        status = "✅"
                        sizes_count = len(result.get('sizes', []))
                        available_sizes = len([s for s in result.get('sizes', []) if s.get('available', False)])
                        size_info = f" | 📏 {available_sizes}/{sizes_count} размеров" if sizes_count > 0 else ""
                    else:
                        status = "❌"
                        size_info = ""

                    logger.info(
                        f"{status} Прогресс: {i + 1}/{len(articles)} - {article} - {name}... - {price}{size_info}")

                except TimeoutException:
                    logger.error(f"⏰ Таймаут выполнения для {article}")
                    results.append({
                        'article': article,
                        'available': False,
                        'product_name': 'Таймаут выполнения',
                        'product_url': f'https://www.ozon.ru/product/{article}',
                        'prices': {
                            'ozon_card_price': 'Нет данных',
                            'regular_price': 'Нет данных'
                        },
                        'sizes': [],
                        'error': 'Task execution timeout'
                    })
                except Exception as e:
                    logger.error(f"❌ Ошибка получения результата для {article}: {e}")
                    results.append({
                        'article': article,
                        'available': False,
                        'product_name': 'Ошибка выполнения',
                        'product_url': f'https://www.ozon.ru/product/{article}',
                        'prices': {
                            'ozon_card_price': 'Нет данных',
                            'regular_price': 'Нет данных'
                        },
                        'sizes': [],
                        'error': str(e)
                    })

        # Статистика
        total_time = time.time() - start_time
        available_count = len([p for p in results if p.get('available', False)])
        unavailable_count = len(results) - available_count

        logger.info(f"📊 Статистика проверки:")
        logger.info(f"   ✅ Доступно: {available_count}")
        logger.info(f"   ❌ Недоступно: {unavailable_count}")
        logger.info(f"   📊 Процент доступности: {(available_count / len(results) * 100):.1f}%")
        logger.info(f"   ⏱️ Общее время: {total_time:.2f} сек")

    except Exception as e:
        logger.error(f"❌ Ошибка в пуле потоков: {e}")

    return results


def save_check_results(results, filename="Проверка на наличие товаров.json"):
    try:
        output_data = {
            'check_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_articles': len(results),
            'available_count': len([p for p in results if p.get('available', False)]),
            'unavailable_count': len([p for p in results if not p.get('available', False)]),
            'products': results
        }

        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(output_data, file, indent=4, ensure_ascii=False)

        logger.info(f"💾 Результаты сохранены в {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения результатов: {e}")
        return False


def main():
    logger.info("🎯 Запуск проверки товаров по артикулам")

    start_time = time.time()

    try:
        articles = load_articles_from_file("Артикулы.txt")

        if not articles:
            logger.error("❌ Не удалось загрузить артикулы для проверки")
            return False

        results = check_products_parallel(articles, max_workers=MAX_WORKERS)

        if results:
            success = save_check_results(results)

            available_products = [p for p in results if p.get('available', False)]
            unavailable_products = [p for p in results if not p.get('available', False)]

            logger.info("🎉 === ПРОВЕРКА ЗАВЕРШЕНА ===")
            logger.info(f"📥 Всего артикулов: {len(results)}")
            logger.info(f"✅ Доступно товаров: {len(available_products)}")
            logger.info(f"❌ Недоступно товаров: {len(unavailable_products)}")

            if available_products:
                logger.info("🛍️ === ДОСТУПНЫЕ ТОВАРЫ ===")
                for i, product in enumerate(available_products):
                    name = product.get('product_name', 'N/A')[:50]
                    ozon_price = product.get('prices', {}).get('ozon_card_price', 'N/A')
                    sizes = product.get('sizes', [])
                    available_sizes = [size['size'] for size in sizes if size.get('available', False)]

                    size_info = f" | Размеры: {', '.join(available_sizes)}" if available_sizes else ""
                    logger.info(f"{i + 1}. {name} - {ozon_price}{size_info}")

            return True
        else:
            logger.error("❌ Не удалось проверить товары")
            return False

    except Exception as e:
        logger.error(f"💥 Критическая ошибка при проверке товаров: {e}")
        return False

    finally:
        total_time = time.time() - start_time
        logger.info(f"⏱️ Общее время выполнения: {total_time:.2f} секунд")


if __name__ == '__main__':
    main()