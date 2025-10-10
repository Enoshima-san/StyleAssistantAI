import asyncio
import json
import datetime
from aiohttp import ClientSession
import config


class ProductChecker:
    def __init__(self):
        self.session = None
        self.headers = config.DEFAULT_HEADERS

    async def init(self) -> None:
        self.session = ClientSession(headers=self.headers)

    async def check_product_availability(self, product_id: int) -> dict:
        """Проверяет доступность товара по артикулу"""
        await self.init()

        try:
            print(f"[INFO] Проверяем товар с артикулом {product_id}...")

            # Основной запрос для получения информации о товаре
            detail_url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={product_id}"

            async with self.session.get(detail_url) as response:
                if response.status != 200:
                    return {
                        "product_id": product_id,
                        "status": "error",
                        "available": False,
                        "message": f"Ошибка API: статус {response.status}",
                        "checked_at": datetime.datetime.now().isoformat()
                    }

                data = await response.json()
                products = data.get("data", {}).get("products", [])

                if not products:
                    return {
                        "product_id": product_id,
                        "status": "not_found",
                        "available": False,
                        "message": "Товар не найден в каталоге",
                        "checked_at": datetime.datetime.now().isoformat()
                    }

                product = products[0]

                # Проверяем доступность по наличию размеров с остатками
                is_available = False
                available_sizes = []
                total_stock = 0

                sizes = product.get("sizes", [])
                for size in sizes:
                    stocks = size.get("stocks", [])
                    size_stock = sum(stock.get("qty", 0) for stock in stocks)
                    if size_stock > 0:
                        is_available = True
                        available_sizes.append({
                            "size_name": size.get("name", "Без размера"),
                            "stock": size_stock
                        })
                        total_stock += size_stock

                # УЛУЧШЕННОЕ ПОЛУЧЕНИЕ ЦЕНЫ - несколько способов
                price = "Не указана"
                discount = None

                if sizes and len(sizes) > 0:
                    price_data = sizes[0].get("price", {})

                    # Способ 1: Основная цена (salePrice)
                    sale_price = price_data.get("product")
                    if sale_price:
                        price = int(sale_price / 100)

                    # Способ 2: Если основная цена не найдена, пробуем totalPrice
                    if price == "Не указана":
                        total_price = price_data.get("total")
                        if total_price:
                            price = int(total_price / 100)

                    # Способ 3: Если все еще не найдена, пробуем priceWithDiscount
                    if price == "Не указана":
                        price_with_discount = product.get("priceWithDiscount")
                        if price_with_discount:
                            price = int(price_with_discount / 100)

                    # Способ 4: Если все еще не найдена, пробуем priceU
                    if price == "Не указана":
                        price_u = product.get("priceU")
                        if price_u:
                            price = int(price_u / 100)

                    # Расчет скидки
                    base_price = price_data.get("basic")
                    sale_price = price_data.get("product")
                    if base_price and sale_price and base_price > sale_price:
                        discount_percent = int((1 - sale_price / base_price) * 100)
                        discount = f"{discount_percent}%"

                # Способ 5: Если цена все еще не найдена, ищем в корне объекта product
                if price == "Не указана":
                    sale_price = product.get("salePrice")
                    if sale_price:
                        price = int(sale_price / 100)

                if price == "Не указана":
                    price_u = product.get("priceU")
                    if price_u:
                        price = int(price_u / 100)

                return {
                    "product_id": product_id,
                    "status": "found",
                    "available": is_available,
                    "total_stock": total_stock,
                    "available_sizes": available_sizes,
                    "brand": product.get("brand", "Не указан"),
                    "name": product.get("name", "Не указано"),
                    "price": price,
                    "discount": discount,
                    "rating": product.get("reviewRating", 0),
                    "feedbacks": product.get("feedbacks", 0),
                    "product_url": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
                    "checked_at": datetime.datetime.now().isoformat(),
                    "message": "В наличии" if is_available else "Нет в наличии"
                }

        except Exception as e:
            return {
                "product_id": product_id,
                "status": "error",
                "available": False,
                "message": f"Ошибка при проверке: {str(e)}",
                "checked_at": datetime.datetime.now().isoformat()
            }
        finally:
            await self.session.close()

    def read_product_ids_from_file(self, filename: str = "Артикулы.txt") -> list:
        """Читает артикулы из текстового файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                product_ids = []
                for line in file:
                    line = line.strip()
                    if line and line.isdigit():
                        product_ids.append(int(line))
                return product_ids
        except FileNotFoundError:
            print(f"❌ Файл {filename} не найден!")
            return []
        except Exception as e:
            print(f"❌ Ошибка при чтении файла: {e}")
            return []

    async def check_multiple_products(self, product_ids: list) -> dict:
        """Проверяет несколько товаров и возвращает сводный результат"""
        print(f"🔍 Начинаем проверку {len(product_ids)} товаров...")

        results = []
        available_count = 0
        not_available_count = 0
        error_count = 0

        for i, product_id in enumerate(product_ids, 1):
            print(f"📦 Проверяем товар {i}/{len(product_ids)} (артикул: {product_id})...")

            result = await self.check_product_availability(product_id)
            results.append(result)

            if result["status"] == "found" and result["available"]:
                available_count += 1
                status_icon = "✅"
            elif result["status"] == "found" and not result["available"]:
                not_available_count += 1
                status_icon = "❌"
            else:
                error_count += 1
                status_icon = "⚠️"

            print(f"   {status_icon} {result['message']}")

            # Небольшая задержка между запросами
            await asyncio.sleep(0.1)

        # Создаем сводный результат
        summary = {
            "check_date": datetime.datetime.now().isoformat(),
            "total_checked": len(product_ids),
            "available": available_count,
            "not_available": not_available_count,
            "errors": error_count,
            "results": results
        }

        return summary

    def save_results_to_json(self, results: dict, filename: str = "Проверка на наличие товаров.json"):
        """Сохраняет результаты в JSON файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"💾 Результаты сохранены в файл: {filename}")
        except Exception as e:
            print(f"❌ Ошибка при сохранении файла: {e}")

    def print_summary(self, results: dict):
        """Выводит сводную информацию о проверке"""
        print("\n" + "=" * 60)
        print("📊 СВОДКА ПРОВЕРКИ ТОВАРОВ")
        print("=" * 60)

        summary = results
        print(f"📅 Дата проверки: {summary['check_date']}")
        print(f"🔢 Всего проверено: {summary['total_checked']} товаров")
        print(f"✅ В наличии: {summary['available']} товаров")
        print(f"❌ Нет в наличии: {summary['not_available']} товаров")
        print(f"⚠️  Ошибки: {summary['errors']} товаров")

        # Выводим список доступных товаров
        available_products = [r for r in summary['results'] if r.get('available')]
        if available_products:
            print(f"\n📦 ДОСТУПНЫЕ ТОВАРЫ ({len(available_products)}):")
            for product in available_products:
                price_display = f"{product['price']} руб." if isinstance(product['price'], int) else product['price']
                discount_display = f" | 🎯 Скидка: {product['discount']}" if product.get('discount') else ""
                print(f"   • {product['brand']} - {product['name']}")
                print(f"     💰 {price_display}{discount_display} | 📦 {product['total_stock']} шт.")
                print(f"     🔗 {product['product_url']}\n")

        print("=" * 60)


async def main():
    """Основная функция для проверки товаров из файла"""
    checker = ProductChecker()

    print("🔍 МАССОВАЯ ПРОВЕРКА ТОВАРОВ WILDBERRIES")
    print("=" * 50)
    print("Чтение артикулов из файла...")

    # Читаем артикулы из файла
    product_ids = checker.read_product_ids_from_file("Артикулы.txt")

    if not product_ids:
        print("❌ Не найдено артикулов для проверки!")
        print("Создайте файл Артикулы.txt и добавьте артикулы (по одному в строку)")
        return

    print(f"📋 Найдено {len(product_ids)} артикулов для проверки")

    # Запускаем проверку
    print("\n🔄 Начинаем проверку товаров...")
    results = await checker.check_multiple_products(product_ids)

    # Выводим сводку
    checker.print_summary(results)

    # Сохраняем результаты
    checker.save_results_to_json(results, "Проверка на наличие товаров.json")

    print("\n✅ Проверка завершена!")


if __name__ == "__main__":
    # Для Windows может потребоваться другой event loop policy
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Программа завершена")