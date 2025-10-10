import time as tm
import re
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchWindowException, WebDriverException

logger = logging.getLogger(__name__)

def page_down(driver):
    # Cкроллинг страницы
    logger.info("Начинаем скроллинг страницы...")

    try:
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            tm.sleep(2)

        logger.info("Скроллинг завершен")
    except Exception as e:
        logger.warning(f"Ошибка скроллинга: {e}")


def extract_price_from_text(text):
    try:
        # Убираем неразрывные пробелы и обычные пробелы
        clean_text = text.replace(' ', '').replace(' ', '').replace('\u202f', '')
        # Ищем числа
        price_match = re.search(r'(\d+)', clean_text)
        if price_match:
            return int(price_match.group(1))
        return None
    except:
        return None


def parse_product_image(driver):
    try:
        high_quality_selectors = [
            'img[src*="/wc2000/"]',
            'img[src*="/wc1500/"]',
            'img[src*="/wc1000/"]',
            'img[src*="/wc800/"]',
            'source[srcset*="/wc2000/"]',
            'source[srcset*="/wc1500/"]',
            'img[data-widget="webGallery"]',
            'div[data-widget="webGallery"] img'
        ]

        for selector in high_quality_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    src = None
                    if element.tag_name == 'source':
                        srcset = element.get_attribute('srcset')
                        if srcset:
                            # Берем первый URL из srcset
                            src = srcset.split(',')[0].split(' ')[0].strip()
                    else:
                        src = element.get_attribute('src')

                    if src and 'http' in src and ('ozon' in src or 'cdn' in src):
                        # Улучшаем качество изображения
                        if '/wc1000/' in src:
                            src = src.replace('/wc1000/', '/wc2000/')
                        elif '/wc500/' in src:
                            src = src.replace('/wc500/', '/wc2000/')
                        elif '/wc300/' in src:
                            src = src.replace('/wc300/', '/wc2000/')
                        return src
            except:
                continue

        # Если не нашли высококачественные, ищем любые изображения товара
        fallback_selectors = [
            'img[alt*="товар"]',
            'img[alt*="product"]',
            'img[src*="cdn1.ozone.ru"]',
            'img[src*="cdn2.ozone.ru"]',
            '.ui-k6 img',
            'img[loading="lazy"]'
        ]

        for selector in fallback_selectors:
            try:
                images = driver.find_elements(By.CSS_SELECTOR, selector)
                for img in images:
                    src = img.get_attribute('src')
                    if src and 'http' in src and ('ozon' in src or 'cdn' in src):
                        if any(size in src for size in ['/wc1000/', '/wc500/', '/wc300/']):
                            src = src.replace('/wc1000/', '/wc2000/').replace('/wc500/', '/wc2000/').replace('/wc300/',
                                                                                                             '/wc2000/')
                        return src
            except:
                continue

        return "Изображение не найдено"

    except Exception as e:
        logger.warning(f"Ошибка парсинга изображения: {e}")
        return "Ошибка загрузки изображения"


def parse_ozon_prices(driver):
    try:
        # Находим основной виджет с ценами
        price_widget = driver.find_element(By.CSS_SELECTOR, 'div[data-widget="webPrice"]')
        widget_text = price_widget.text
        logger.info(f"Текст виджета цен: {widget_text}")

        # Разделяем текст на строки
        lines = [line.strip() for line in widget_text.split('\n') if line.strip()]

        ozon_card_price = None
        regular_price = None
        all_prices = []

        # Собираем все цены и определяем их тип
        for i, line in enumerate(lines):
            price = extract_price_from_text(line)
            if price and price > 10:  # Фильтруем реальные цены
                all_prices.append(price)

                # Определяем тип цены по контексту
                line_lower = line.lower()
                if 'ozon карт' in line_lower or 'картой' in line_lower or 'с картой' in line_lower:
                    ozon_card_price = price
                elif 'без ozon карт' in line_lower or 'обычная' in line_lower or 'без карты' in line_lower:
                    regular_price = price

        # Если нашли цены, но не определили их тип
        if all_prices:
            # Берем минимальную цену как Ozon Card, максимальную как обычную
            min_price = min(all_prices)
            max_price = max(all_prices)

            if not ozon_card_price:
                ozon_card_price = min_price
            if not regular_price:
                regular_price = max_price

        # Если нашли только одну цену
        if ozon_card_price and not regular_price:
            regular_price = ozon_card_price
        elif regular_price and not ozon_card_price:
            ozon_card_price = regular_price

        logger.info(f"💰 Найденные цены: Ozon Card - {ozon_card_price}, Обычная - {regular_price}")
        return ozon_card_price, regular_price

    except Exception as e:
        logger.warning(f"Ошибка парсинга виджета цен: {e}")
        return None, None


def parse_product_characteristics(driver):
    all_characteristics = {}
    basic_characteristics = {
        'material': 'Не указано',
        'material_composition': 'Не указано',
        'lining_material': 'Не указано',
        'color': 'Не указано',
        'type': 'Не указано'
    }

    try:
        logger.info("🔍 Начинаем парсинг ВСЕХ характеристик товара...")
        tm.sleep(3)
        driver.execute_script("window.scrollTo(0, 1000);")
        tm.sleep(2)

        characteristics_element = None
        selectors = [
            'div[data-widget="webCharacteristics"]',
            'div[data-widget="webCharacteristics"] > div',
            '.ui-k6',  # Общий класс характеристик
            'div[data-widget*="characteristic"]',
            'div[class*="characteristic"]',
            'div[class*="specification"]',
            'dl',  # Структура definition list
            '.a2g0',  # Класс характеристик Ozon
            'section[aria-label*="арактеристик"]',  # По aria-label
        ]

        for selector in selectors:
            try:
                characteristics_element = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.info(f"✅ Найден блок характеристик через селектор: {selector}")
                break
            except TimeoutException:
                continue

        if not characteristics_element:
            logger.warning("❌ Блок характеристик не найден через основные селекторы, пробуем альтернативные методы...")

            # АЛЬТЕРНАТИВНЫЙ ПОИСК: ищем любой элемент с текстом "характеристики"
            try:
                characteristics_heading = driver.find_element(By.XPATH,
                                                              "//*[contains(text(), 'арактеристик') or contains(text(), 'арактеристики')]")
                characteristics_element = characteristics_heading.find_element(By.XPATH, "./following-sibling::div[1]")
                logger.info("✅ Найден блок характеристик через текстовый поиск")
            except:
                logger.warning("❌ Блок характеристик не найден")
                return basic_characteristics

        # ДОПОЛНИТЕЛЬНЫЙ СКРОЛЛИНГ ДЛЯ АКТИВАЦИИ ДИНАМИЧЕСКОГО КОНТЕНТА
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                  characteristics_element)
            tm.sleep(2)
        except:
            pass

        # Получаем весь текст характеристик
        full_text = characteristics_element.text
        logger.info(f"📋 Текст характеристик: {full_text[:500]}...")

        # СПОСОБ 1: Парсим структурированные характеристики (ключ-значение)
        try:
            # Ищем все возможные контейнеры характеристик
            containers = [
                'dl',
                'div[class*="item"]',
                'div[class*="row"]',
                'div[class*="line"]',
                'div[class*="property"]',
                'div'
            ]

            for container in containers:
                try:
                    characteristic_items = characteristics_element.find_elements(By.CSS_SELECTOR, container)

                    for item in characteristic_items:
                        try:
                            item_html = item.get_attribute('outerHTML')
                            item_text = item.text.strip()

                            if not item_text or len(item_text) < 5:
                                continue

                            # Структура 1: <dt>Ключ</dt><dd>Значение</dd>
                            if 'dt' in item_html and 'dd' in item_html:
                                key_elements = item.find_elements(By.TAG_NAME, 'dt')
                                value_elements = item.find_elements(By.TAG_NAME, 'dd')

                                for key_elem, value_elem in zip(key_elements, value_elements):
                                    key = key_elem.text.strip()
                                    value = value_elem.text.strip()
                                    if (key and value and
                                            len(key) < 100 and
                                            len(value) < 100 and
                                            key not in all_characteristics):
                                        all_characteristics[key] = value
                                        logger.info(f"   📝 {key}: {value}")

                            # Структура 2: div с текстом в несколько строк
                            else:
                                lines = [line.strip() for line in item_text.split('\n') if line.strip()]
                                if len(lines) >= 2:
                                    for i in range(len(lines) - 1):
                                        key = lines[i].strip()
                                        value = lines[i + 1].strip()
                                        if (key and value and
                                                '______' not in key and
                                                '______' not in value and
                                                len(key) < 100 and
                                                len(value) < 100 and
                                                key not in all_characteristics):
                                            all_characteristics[key] = value
                                            logger.info(f"   📝 {key}: {value}")
                                            break
                        except Exception as e:
                            continue
                except:
                    continue

        except Exception as e:
            logger.warning(f"⚠️ Ошибка структурированного парсинга: {e}")

        # СПОСОБ 2: Парсим по строкам (резервный метод)
        if not all_characteristics:
            logger.info("Пробуем парсинг по строкам...")
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]

            i = 0
            while i < len(lines) - 1:
                current_line = lines[i]
                next_line = lines[i + 1] if i + 1 < len(lines) else ""

                # Пропускаем разделители и заголовки
                if (not current_line or
                        '______' in current_line or
                        current_line.isupper() or
                        len(current_line) > 100 or
                        current_line.endswith(':') or
                        'характеристик' in current_line.lower()):
                    i += 1
                    continue

                # Проверяем, является ли текущая строка ключом, а следующая - значением
                if (next_line and
                        '______' not in next_line and
                        len(next_line) < 100 and
                        not next_line.isupper() and
                        not next_line.endswith(':') and
                        current_line not in all_characteristics and
                        len(current_line) > 2 and len(next_line) > 2):

                    all_characteristics[current_line] = next_line
                    logger.info(f"   📝 {current_line}: {next_line}")
                    i += 2  # Пропускаем обе строки
                else:
                    i += 1

        # СПОСОБ 3: Регулярные выражения для поиска ключ-значение
        if not all_characteristics:
            logger.info("Пробуем парсинг через регулярные выражения...")

            # Ищем паттерны "Ключ: Значение" или "Ключ - Значение"
            patterns = [
                r'(.+?)[:\—]\s*(.+?)(?=\n|$)',
                r'(.+?)\n\s*(.+?)(?=\n|$)',
                r'^(.+?)\s{2,}(.+?)$'  # Два или более пробелов как разделитель
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, full_text, re.MULTILINE)
                for match in matches:
                    key = match.group(1).strip()
                    value = match.group(2).strip()

                    if (key and value and
                            '______' not in key and
                            '______' not in value and
                            len(key) < 100 and
                            len(value) < 100 and
                            key not in all_characteristics and
                            len(key) > 2 and len(value) > 2):
                        all_characteristics[key] = value
                        logger.info(f"   📝 {key}: {value}")

        # ОБНОВЛЯЕМ ОСНОВНЫЕ ХАРАКТЕРИСТИКИ ИЗ ВСЕХ НАЙДЕННЫХ
        for key, value in all_characteristics.items():
            key_lower = key.lower()

            # Материал
            if 'материал' in key_lower and 'состав' not in key_lower and 'подклад' not in key_lower:
                basic_characteristics['material'] = value

            # Состав материала
            elif 'состав' in key_lower:
                basic_characteristics['material_composition'] = value

            # Материал подкладки
            elif 'подклад' in key_lower:
                basic_characteristics['lining_material'] = value

            # Цвет
            elif 'цвет' in key_lower:
                basic_characteristics['color'] = value

            # Тип (только точное совпадение)
            elif key_lower == 'тип':
                basic_characteristics['type'] = value

        # ДОБАВЛЯЕМ ВСЕ ХАРАКТЕРИСТИКИ В ОСНОВНЫЕ ДЛЯ ВЫВОДА
        basic_characteristics['all_characteristics'] = all_characteristics

    except Exception as e:
        logger.warning(f"❌ Ошибка парсинга характеристик: {e}")
        basic_characteristics['all_characteristics'] = {}

    logger.info(f"📋 Результат парсинга характеристик:")
    logger.info(f"   🧵 Материал: '{basic_characteristics['material']}'")
    logger.info(f"   📊 Состав: '{basic_characteristics['material_composition']}'")
    logger.info(f"   🧵 Подкладка: '{basic_characteristics['lining_material']}'")
    logger.info(f"   🎨 Цвет: '{basic_characteristics['color']}'")
    logger.info(f"   📝 Тип: '{basic_characteristics['type']}'")
    logger.info(f"   📋 Всего характеристик найдено: {len(all_characteristics)}")

    return basic_characteristics


def safe_window_management(driver, url):
    try:
        # Сохраняем текущее окно
        original_window = driver.current_window_handle
        # Загружаем URL в текущем окне
        driver.get(url)
        tm.sleep(3)

        return original_window, True

    except Exception as e:
        logger.error(f"Ошибка управления окнами: {e}")
        return None, False


def collect_product_info(driver, url=''):
    logger.info(f"Парсим товар: {url}")

    product_data = {
        'product_id': 'unknown',
        'product_name': 'Не удалось получить название',
        'product_ozon_card_price': 'Нет данных',
        'product_regular_price': 'Нет данных',
        'product_image_url': 'Нет данных',
        'product_url': url,
        'material': 'Не указано',
        'material_composition': 'Не указано',
        'lining_material': 'Не указано',
        'color': 'Не указано',
        'type': 'Не указано',
        'all_characteristics': {}
    }

    try:
        driver.get(url)
        tm.sleep(3)

        # Получаем ID из URL
        match = re.search(r'/product/([^/?]+)', url)
        if match:
            product_data['product_id'] = match.group(1)

        # Поиск названия товара
        try:
            name_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-widget="webProductHeading"] h1'))
            )
            product_data['product_name'] = name_element.text.strip()
        except TimeoutException:
            try:
                name_element = driver.find_element(By.TAG_NAME, 'h1')
                product_data['product_name'] = name_element.text.strip()
            except:
                logger.warning("Не удалось найти название товара")

        # Парсинг изображения
        product_data['product_image_url'] = parse_product_image(driver)

        # Парсинг цен
        ozon_card_price, regular_price = parse_ozon_prices(driver)

        # Если не нашли через виджет, пробуем альтернативные методы поиска цены
        if not ozon_card_price or not regular_price:
            logger.info("Пробуем альтернативные методы поиска цен...")
            all_price_elements = driver.find_elements(By.XPATH, '//*[contains(text(), "₽")]')
            prices_found = []

            for element in all_price_elements:
                text = element.text
                price = extract_price_from_text(text)
                if price and price > 100:  # Фильтруем реальные цены
                    # Проверяем, не перечеркнута ли цена
                    try:
                        # Ищем перечеркнутые цены
                        parent = element.find_element(By.XPATH, './..')
                        parent_html = parent.get_attribute('outerHTML')
                        if 'text-decoration: line-through' not in parent_html and 'line-through' not in parent_html:
                            prices_found.append(price)
                    except:
                        prices_found.append(price)

            if prices_found:
                prices_found = list(set(prices_found))
                prices_found.sort()

                # Берем минимальную цену как Ozon Card
                if prices_found:
                    min_price = min(prices_found)
                    ozon_card_price = min_price
                    # Если есть другие цены, берем максимальную как обычную, иначе дублируем
                    if len(prices_found) > 1:
                        regular_price = max(prices_found)
                    else:
                        regular_price = min_price

        # Записываем результаты
        if ozon_card_price:
            product_data['product_ozon_card_price'] = f"{ozon_card_price} ₽"
        if regular_price:
            product_data['product_regular_price'] = f"{regular_price} ₽"

        # Если одна из цен отсутствует, дублируем имеющуюся
        if product_data['product_ozon_card_price'] == 'Нет данных' and product_data[
            'product_regular_price'] != 'Нет данных':
            product_data['product_ozon_card_price'] = product_data['product_regular_price']
        elif product_data['product_regular_price'] == 'Нет данных' and product_data[
            'product_ozon_card_price'] != 'Нет данных':
            product_data['product_regular_price'] = product_data['product_ozon_card_price']

        # Парсинг характеристик
        characteristics = parse_product_characteristics(driver)
        product_data.update(characteristics)

        logger.info(
            f"✅ Найдены цены: Ozon Card - {product_data['product_ozon_card_price']}, Обычная - {product_data['product_regular_price']}")
        logger.info(f"🖼️ Изображение: {product_data['product_image_url'][:100]}...")
        logger.info(f"📋 Характеристики: Материал - {product_data['material']}, "
                    f"Состав - {product_data['material_composition']}, "
                    f"Подкладка - {product_data['lining_material']}")

    except Exception as e:
        logger.error(f"❌ Ошибка при парсинге {url}: {e}")
        product_data['error'] = str(e)

    return product_data