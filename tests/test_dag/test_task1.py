from dags.test_dag import task_1


def test_task1():
    value = task_1()
    assert value == "first_task"
