from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

# src доступен через PYTHONPATH=/opt/airflow/src в Docker
SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def task_ingest() -> dict:
    from ingestion.run_ingestion import run_all

    return run_all()


def task_transform() -> str:
    from etl.transform import transform_raw_to_staging

    path = transform_raw_to_staging()
    return str(path)


def task_load() -> int:
    from etl.load import load_staging_to_db

    return load_staging_to_db()


def task_analytics() -> dict:
    from etl.analytics import refresh_price_history
    from alerts.notifier import check_price_alerts

    history_rows = refresh_price_history()
    alerts = check_price_alerts()
    return {"history_rows": history_rows, "alerts_count": len(alerts)}


with DAG(
    dag_id="price_monitoring_pipeline",
    default_args=default_args,
    description="Ingest → Transform → Load → Analytics для мониторинга цен",
    schedule_interval="0 */6 * * *", # каждые 6 часов
    start_date=__import__("datetime").datetime(2024, 1, 1),
    catchup=False,
    tags=["price_monitoring", "etl", "marketplace"],
) as dag:
    ingest = PythonOperator(task_id="ingest_raw_data", python_callable=task_ingest)
    transform = PythonOperator(task_id="transform_staging", python_callable=task_transform)
    load = PythonOperator(task_id="load_to_postgres", python_callable=task_load)
    analytics = PythonOperator(task_id="analytics_and_alerts", python_callable=task_analytics)

    ingest >> transform >> load >> analytics
