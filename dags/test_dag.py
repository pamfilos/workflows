from datetime import timedelta

import airflow
from airflow import DAG
from airflow.operators.python_operator import PythonOperator


def task_1():
    return "first_task"


def task_2():
    return "second_task"


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": airflow.utils.dates.days_ago(0),
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG("test_dag", default_args=default_args, schedule_interval="@daily") as dag:

    t1 = PythonOperator(task_id="task_1", python_callable=task_1)

    t2 = PythonOperator(task_id="task_2", python_callable=task_2)

    t1 >> t2
