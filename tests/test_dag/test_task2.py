from dags.test_dag import task_2


def test_task2():
    value = task_2()
    assert value == "second_task"
