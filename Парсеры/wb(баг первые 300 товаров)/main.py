import asyncio
import json
import datetime
from aiohttp import ClientSession
import config


class WildBerriesParser:
    def __init__(self):
        self.session = None
        self.headers = config.DEFAULT_HEADERS
        self._semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)
        self.run_count = 0

    async def init(self) -> None:
        self.session = ClientSession(headers=self.headers)

    def __get_image_links(self, product_id: int, pics_count: int) -> list:
        if not pics_count:
            return ["Не указаны"]
        _short_id = product_id // 100000
        if 0 <= _short_id <= 143:
            basket = '01'
        elif 144 <= _short_id <= 287:
            basket = '02'
        elif 288 <= _short_id <= 431:
            basket = '03'
        elif 432 <= _short_id <= 719:
            basket = '04'
        elif 720 <= _short_id <= 1007:
            basket = '05'
        elif 1008 <= _short_id <= 1061:
            basket = '06'
        elif 1062 <= _short_id <= 1115:
            basket = '07'
        elif 1116 <= _short_id <= 1169:
            basket = '08'
        elif 1170 <= _short_id <= 1313:
            basket = '09'
        elif 1314 <= _short_id <= 1601:
            basket = '10'
        elif 1602 <= _short_id <= 1655:
            basket = '11'
        elif 1656 <= _short_id <= 1919:
            basket = '12'
        elif 1920 <= _short_id <= 2045:
            basket = '13'
        elif 2046 <= _short_id <= 2189:
            basket = '14'
        elif 2190 <= _short_id <= 2405:
            basket = '15'
        else:
            basket = '16'
        image_links = [
            f"https://basket-{basket}.wbbasket.ru/vol{_short_id}/part{product_id // 1000}/{product_id}/images/big/{i}.webp"
            for i in range(1, pics_count + 1)
        ]
        return image_links

    async def _fetch_details(self, product_id: int) -> tuple[int, dict]:
        # Ограничиваем количество одновременных запросов
        async with self._semaphore:
            if config.REQUEST_DELAY > 0:
                await asyncio.sleep(config.REQUEST_DELAY)

            details = {}
            part = product_id // 1000
            vol = part // 100  # или product_id // 100_000

            # Перебираем возможные basket
            for basket_num in range(1, 33):  # 1 -> '01', 2 -> '02', ..., 10 -> '10', ...
                basket = f"{basket_num:02d}"  # Форматируем как двузначное число с ведущим нулём
                basket_card_url = f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/info/ru/card.json"
                try:
                    async with self.session.get(basket_card_url) as response:  # headers уже в сессии
                        if response.status == 200:
                            text = await response.text()
                            if text.strip():
                                data = json.loads(text)
                                options_list = data.get("options", [])
                                for opt in options_list:
                                    name = opt.get("name")
                                    value = opt.get("value")
                                    if name and value:
                                        if isinstance(value, list):
                                            value = ", ".join(str(v) for v in value)
                                        elif isinstance(value, dict):
                                            value = str(value)
                                        details[name] = value
                                # Если нашли хоть одну характеристику в card.json, возвращаем
                                if details:
                                    print(f"[INFO] Найдены характеристики для {product_id} через basket-{basket}.")
                                    return product_id, details
                            else:
                                print(
                                    f"[INFO] basket card.json (basket-{basket}) для {product_id} вернул пустой ответ, пробуем следующий basket или tech-card.")
                        # else: # Для отладки, можно раскомментировать
                        #     print(f"[DEBUG] basket card.json (basket-{basket}) для {product_id} вернул статус {response.status}")
                except Exception as e:
                    # print(f"[ERROR] Ошибка при запросе basket card.json (basket-{basket}) для {product_id}: {e}. Пробуем следующий basket или tech-card.")
                    pass  # Игнорируем ошибки для конкретного basket и пробуем следующий

            print(f"[INFO] Не удалось найти характеристики через basket card.json для {product_id}, пробуем tech-card.")

            # 2. Попробуем получить через tech-card
            tech_card_url = f"https://card.wb.ru/cards/v1/tech-card?nm={product_id}"
            try:
                async with self.session.get(tech_card_url) as response:  # headers уже в сессии
                    if response.status == 200:
                        text = await response.text()
                        if text.strip():
                            data = json.loads(text)
                            tech_card_data = data.get("data", {})
                            if tech_card_data:
                                characteristics_list = tech_card_data.get("characteristics", [])
                                for ch in characteristics_list:
                                    name = ch.get("name")
                                    value = ch.get("value")
                                    if name and value:
                                        if isinstance(value, list):
                                            value = ", ".join(str(v) for v in value)
                                        elif isinstance(value, dict):
                                            value = str(value)
                                        details[name] = value
                                # Если нашли хоть одну характеристику в tech-card, возвращаем
                                if details:
                                    print(f"[INFO] Найдены характеристики для {product_id} через tech-card.")
                                    return product_id, details
                                else:
                                    print(
                                        f"[INFO] tech-card для {product_id} не содержит характеристик, пробуем v2/detail.")
                            else:
                                print(f"[INFO] tech-card для {product_id} не содержит данных, пробуем v2/detail.")
                        else:
                            print(f"[INFO] tech-card для {product_id} вернул пустой ответ, пробуем v2/detail.")
                    else:
                        print(f"[INFO] tech-card для {product_id} вернул статус {response.status}, пробуем v2/detail.")
            except Exception as e:
                print(f"[ERROR] Ошибка при запросе tech-card для {product_id}: {e}. Пробуем v2/detail.")

            # 3. Если basket card.json и tech-card не сработали или не дали результатов, используем v2/detail
            v2_detail_url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={product_id}"
            try:
                async with self.session.get(v2_detail_url) as response:  # headers уже в сессии
                    if response.status != 200:
                        print(
                            f"[WARN] Не удалось получить характеристики для {product_id} через v2/detail, статус {response.status}")
                        return product_id, {"Характеристики": "Не найдены"}
                    text = await response.text()
                    if not text.strip():
                        print(f"[WARN] Пустой ответ для {product_id} через v2/detail")
                        return product_id, {"Характеристики": "Не найдены"}
                    data = json.loads(text)
            except Exception as e:
                print(f"[ERROR] Ошибка при запросе v2/detail для {product_id}: {e}")
                return product_id, {"Характеристики": "Не найдены"}

            products = data.get("data", {}).get("products", [])
            if not products:
                return product_id, {"Характеристики": "Не найдены"}

            product = products[0]

            # Источник 1: characteristics
            for ch in product.get("characteristics", []):
                details[ch.get("name")] = ch.get("value")

            # Источник 2: extended.data
            for ch in product.get("extended", {}).get("data", []):
                details[ch.get("name")] = ch.get("value")

            # Источник 3: options
            for option in product.get("options", []):
                name = option.get("name")
                value = option.get("value")
                if name and value:
                    details[name] = value

            # Источник 4: sizes[0].tech_sizes
            sizes = product.get("sizes", [])
            if sizes and isinstance(sizes, list) and len(sizes) > 0:
                tech_sizes = sizes[0].get("tech_sizes", [])
                for tech_size in tech_sizes:
                    name = tech_size.get("name")
                    value = tech_size.get("value")
                    if name and value:
                        details[name] = value

            # Возвращаем словарь с характеристиками или сообщение, если ничего не нашли
            #print(f"[INFO] Найдены характеристики для {product_id} через v2/detail (или другие источники внутри).")
            return product_id, details if details else {"Характеристики": "Не найдены"}


    # Основной метод получения деталей
    async def get_product_details(self, product_ids: list[int]) -> dict[int, dict]:
        """Получает характеристики для списка product_id асинхронно."""
        tasks = [self._fetch_details(pid) for pid in product_ids]
        results = await asyncio.gather(*tasks)
        return {pid: details for pid, details in results}

    async def from_search(self, keyword: str) -> dict:
        all_products = []
        json_data = []

        print(f"[INFO] Начинаю поиск по запросу: '{keyword}'")

        page = 1
        while True:
            print(f"[INFO] Запрашиваю страницу {page}...")
            url = config.SEARCH_URL_TEMPLATE.format(page=page, keyword=keyword)  # Используем шаблон из конфига
            try:
                async with self.session.get(url) as response:  # headers уже в сессии
                    data = json.loads(await response.text())
            except Exception as e:
                print(f"[ERROR] Ошибка при поиске {keyword} на странице {page}: {e}")
                break

            products_on_page = data.get("data", {}).get("products", [])
            if not products_on_page:
                print(f"[INFO] Страница {page} пуста или больше нет товаров. Завершение поиска.")
                # Если на странице нет товаров, значит, это последняя страница
                break

            all_products.extend(products_on_page)
            #print(f"[INFO] Найдено {len(products_on_page)} товаров на странице {page}.")

            if config.SEARCH_PAGES != "ALL":
                if page >= config.SEARCH_PAGES:
                    print(f"[INFO] Достигнуто заданное количество страниц ({config.SEARCH_PAGES}). Завершение поиска.")
                    break

            page += 1
            # Небольшая задержка между запросами поиска, чтобы не перегружать API
            await asyncio.sleep(1)

        product_ids = [p.get("id") for p in all_products if p.get("id")]
        if not product_ids:
            print("[WARN] Не найдено ни одного product_id.")
            return {"search_query": keyword, "total_products": 0, "products": []}

        print(f"[INFO] Найдено {len(product_ids)} товаров для получения деталей. Запускаю асинхронный парсинг...")
        details_map = await self.get_product_details(product_ids)

        for product in all_products:
            product_id = product.get("id")
            if not product_id:
                print("[WARN] У товара отсутствует product_id, пропускаем...")
                continue
            details = details_map.get(product_id, {"Характеристики": "Не найдены"})
            price = "Не указана"
            if product.get("sizes") and len(product["sizes"]) > 0:
                price_data = product["sizes"][0].get("price", {})
                sale_price = price_data.get("product")
                if sale_price:
                    price = int(sale_price / 100)
            color = "Не указан"
            if product.get("colors") and len(product["colors"]) > 0:
                color = product["colors"][0].get("name", "Не указан")
            sizes = "Не указан"
            if product.get("sizes") and len(product["sizes"]) > 0:
                size_names = [size.get("name", "") for size in product["sizes"]]
                sizes = ", ".join(filter(None, size_names))
            pics_count = product.get("pics", 0)
            image_links = self.__get_image_links(product_id, pics_count)

            product_data = {
                "brand": product.get("brand"),
                "brandId": product.get("brandId"),
                "feedbacks": product.get("feedbacks"),
                "id": product_id,
                "name": product.get("name"),
                "reviewRating": product.get("reviewRating"),
                "price": price,
                "color": color,
                "sizes": sizes,
                "image_links": image_links,
                "pics_count": pics_count,
                "product_url": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
                "characteristics": details
            }
            json_data.append(product_data)


        with open(config.JSON_OUTPUT_FILE, "w", encoding="utf-8") as json_file:  # Используем имя файла из конфига
            json.dump({
                "search_query": keyword,  # keyword передаётся в from_search
                "total_products": len(json_data),
                "products": json_data
            }, json_file, indent=2, ensure_ascii=False, default=str)

        print(f"Парсинг завершен! Найдено товаров: {len(json_data)}")
        print(f"Файл сохранён: {config.JSON_OUTPUT_FILE}")
        return {
            "search_query": keyword,
            "total_products": len(json_data),
            "products": json_data
        }

    async def single_run(self) -> dict:
        """Одиночный запуск парсера"""
        self.run_count += 1
        print(f"\n{'=' * 50}")
        print(f"ЗАПУСК ПАРСЕРА #{self.run_count}")
        print(f"Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Запрос: '{config.SEARCH_QUERY}'")
        print(f"{'=' * 50}")

        await self.init()
        result = await self.from_search(config.SEARCH_QUERY)
        await self.session.close()

        print(f"\n--- Статистика парсинга #{self.run_count} для '{config.SEARCH_QUERY}' ---")
        print(f"Всего товаров: {result['total_products']}")
        print(f"Время завершения: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("--- Парсинг завершён ---")

        return result


async def automated_parser():
    """Функция для автоматизированного запуска парсера"""
    wbp = WildBerriesParser()

    if not config.AUTO_RUN:
        # Одиночный запуск, если автоматизация выключена
        await wbp.single_run()
        return

    print("🚀 АВТОМАТИЗИРОВАННЫЙ ПАРСЕР ЗАПУЩЕН")
    print(f"📊 Интервал: {config.RUN_INTERVAL_MINUTES} минут(ы)")
    print(f"🔢 Максимальное количество запусков: {config.MAX_RUNS or 'бесконечно'}")
    print(f"🔍 Поисковый запрос: '{config.SEARCH_QUERY}'")
    print("=" * 60)

    while True:
        if config.MAX_RUNS and wbp.run_count >= config.MAX_RUNS:
            print(f"\n✅ Достигнуто максимальное количество запусков ({config.MAX_RUNS}). Завершение работы.")
            break

        try:
            await wbp.single_run()
        except Exception as e:
            print(f"❌ Ошибка при запуске парсера: {e}")
            print(f"⏰ Повторная попытка через {config.RUN_INTERVAL_MINUTES} минут(ы)")

        if config.MAX_RUNS and wbp.run_count >= config.MAX_RUNS:
            break

        print(f"\n⏰ Ожидание следующего запуска через {config.RUN_INTERVAL_MINUTES} минут(ы)...")
        await asyncio.sleep(config.RUN_INTERVAL_MINUTES * 60)  # Конвертируем минуты в секунды


async def main() -> None:
    """Основная функция"""
    await automated_parser()


if __name__ == "__main__":
    asyncio.run(main())