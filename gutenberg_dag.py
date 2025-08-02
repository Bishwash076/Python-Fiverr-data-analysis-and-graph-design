from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def dummy_etl():
    print("Running ETL pipeline...")

with DAG(dag_id="gutenberg_dag", start_date=datetime(2023, 1, 1), schedule_interval="@daily", catchup=False) as dag:
    task = PythonOperator(
        task_id="run_etl",
        python_callable=dummy_etl
    )
