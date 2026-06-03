from ingestion.base import RawProductRecord

DEMO_CATALOG: dict[str, list[dict]] = {
    "wildberries": [
        {"external_id": "WB-10001", "name": "Смартфон Galaxy A54 128GB", "category": "Смартфоны", "brand": "Samsung", "price": 32990},
        {"external_id": "WB-10002", "name": "Ноутбук IdeaPad 15 8GB/512GB", "category": "Ноутбуки", "brand": "Lenovo", "price": 54990},
        {"external_id": "WB-10003", "name": "Кроссовки беговые Run Flex", "category": "Обувь", "brand": "Nike", "price": 8990},
        {"external_id": "WB-10004", "name": "Пылесос робот CleanBot S2", "category": "Бытовая техника", "brand": "Xiaomi", "price": 19990},
        {"external_id": "WB-10005", "name": "Наушники WH-1000XM5", "category": "Аудио", "brand": "Sony", "price": 27990},
    ],
    "ozon": [
        {"external_id": "OZ-20001", "name": "Смартфон Galaxy A54 128GB", "category": "Смартфоны", "brand": "Samsung", "price": 31990},
        {"external_id": "OZ-20002", "name": "Планшет Tab S9 FE Wi-Fi", "category": "Планшеты", "brand": "Samsung", "price": 45990},
        {"external_id": "OZ-20003", "name": "Монитор 27\" IPS 144Hz", "category": "Мониторы", "brand": "LG", "price": 24990},
        {"external_id": "OZ-20004", "name": "Умные часы Watch Fit 3", "category": "Гаджеты", "brand": "Huawei", "price": 12990},
        {"external_id": "OZ-20005", "name": "Кофеварка рожковая Barista", "category": "Бытовая техника", "brand": "DeLonghi", "price": 34990},
    ],
    "yandex_market": [
        {"external_id": "YM-30001", "name": "Смартфон Galaxy A54 128GB", "category": "Смартфоны", "brand": "Samsung", "price": 33490},
        {"external_id": "YM-30002", "name": "Игровая мышь G Pro X", "category": "Периферия", "brand": "Logitech", "price": 9990},
        {"external_id": "YM-30003", "name": "Микроволновка Solo 23л", "category": "Бытовая техника", "brand": "Samsung", "price": 11990},
        {"external_id": "YM-30004", "name": "Электросамокат Urban 25км/ч", "category": "Транспорт", "brand": "Kugoo", "price": 42990},
        {"external_id": "YM-30005", "name": "Фен для волос Ionic Pro", "category": "Красота", "brand": "Dyson", "price": 38990},
    ],
}


def build_demo_records(source: str, price_jitter_pct: float = 0.03) -> list[RawProductRecord]:
    import random

    items = DEMO_CATALOG[source]
    records: list[RawProductRecord] = []
    for item in items:
        jitter = 1 + random.uniform(-price_jitter_pct, price_jitter_pct)
        price = round(item["price"] * jitter, 2)
        records.append(
            RawProductRecord(
                external_id=item["external_id"],
                name=item["name"],
                category=item["category"],
                brand=item["brand"],
                source=source,
                price=price,
                currency="RUB",
                availability=random.random() > 0.08,
            )
        )
    return records
