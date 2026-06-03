from __future__ import annotations

import logging
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ingestion.base import RawProductRecord
from ingestion.demo_data import build_demo_records

logger = logging.getLogger(__name__)


def collect_ozon_dynamic(headless: bool = True, limit: int = 5) -> list[RawProductRecord]:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    records: list[RawProductRecord] = []
    try:
        driver.get("https://www.ozon.ru/search/?text=смартфон")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/product/']"))
        )
        time.sleep(2)
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")[:limit]
        for idx, link in enumerate(links):
            name = link.text.strip() or f"Ozon dynamic {idx}"
            records.append(
                RawProductRecord(
                    external_id=f"oz-sel-{idx}",
                    name=name[:512],
                    category="unknown",
                    brand="unknown",
                    source="ozon",
                    price=0.0,
                )
            )
    except Exception as exc:
        logger.warning("Selenium Ozon failed: %s", exc)
        return build_demo_records("ozon")
    finally:
        driver.quit()
    return records or build_demo_records("ozon")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = collect_ozon_dynamic()
    print(f"Collected {len(result)} records")
