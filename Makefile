export PYTHON_VERSION = 3.8.13


WEBSERVER_PID=airflow-webserver-monitor.pid
TRIGGERER_PID=airflow-triggerer.pid
SCHEDULER_PID=airflow-scheduler.pid
WORKER_PID=airflow-worker.pid
FLOWER_PID=airflow-flower.pid

init:
	pyenv global $(PYTHON_VERSION)
	pyenv install ${PYTHON_VERSION}
	pyenv virtualenv ${PYTHON_VERSION} workflows
	pyenv activate workflows
	export AIRFLOW_HOME=${PWD}

start: compose sleep airflow

sleep:
	sleep 10

buckets:
	docker-compose up -d create_buckets

airflow:
	airflow db init
	airflow webserver -D
	airflow triggerer -D
	airflow scheduler -D
	airflow celery worker -D
	airflow celery flower -D
	echo -e "\033[0;32m Airflow Started. \033[0m"

compose:
	docker-compose up -d redis postgres sftp s3 create_buckets
	sleep 5

stop:
	docker-compose down
	cat $(WEBSERVER_PID) | xargs kill
	cat $(TRIGGERER_PID) | xargs kill
	cat $(SCHEDULER_PID) | xargs kill
	cat $(WORKER_PID) | xargs kill
	cat $(FLOWER_PID) | xargs kill
	rm *.out *.err *.log
	echo -e "\033[0;32m Airflow Stoped. \033[0m"
