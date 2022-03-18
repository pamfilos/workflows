FROM apache/airflow:2.2.4-python3.7

ENV PYTHONBUFFERED=0 
ENV AIRFLOW_UID=501

COPY requirements.txt ./requirements.txt
COPY dags ./dags
COPY plugins ./plugins
COPY logs ./logs

RUN pip install --no-cache-dir -r requirements.txt -r requirements-test.txt
USER airflow
