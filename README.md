[![codecov](https://codecov.io/gh/cern-sis/workflows/branch/main/graph/badge.svg?token=00LZLXO5OD)](https://codecov.io/gh/cern-sis/workflows)

# workflows



## Run with docker-compose

The easiest way to run the project is run in with docker compose.
For it docker-compose has to be installed.After just run in it the command bellow:

```
docker-compose up --build
```

## Run it locally

We need to install airflow.

1. First, we should create virtual environment with pyenv:

```
    pyenv global 3.7.10
    export PYTHON_VERSION=3.7.10
    pyenv install $PYTHON_VERSION
    pyenv virtualenv $PYTHON_VERSION workflows
    pyenv activate workflows
```

3. Set airflow home directory:

```
export AIRFLOW_HOME=/path/to/cloned/repo
```

4. Install all required dependencies for a project. We need 3 requirements files, when we're running the project locally. First file (requirements.py) has all additional dependencies required to run the tasks correctly (connecting to ftputil, boto3 and etc.), the second one installs requirememnts for testing, such as pytest, the third- (requirements_airflow.py) installs Airflow itself and constraints needed for it. The the third file is not needed when we're running the procject on Docker, because we're using Apache Airflow Docker image:
   `pip install requirements.txt -r requirements-test.txt -r requirements-airflow.txt`
5. Run standalone command. The Standalone command will initialise the database, make a user, and start all components for you:

```
airflow standalone
```

## Access UI

Airflow UI will be rinning on localhost:8080.
More details about Airflow installation and running can be found [here](https://airflow.apache.org/docs/apache-airflow/stable/start/local.html)
