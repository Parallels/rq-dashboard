import time


def func_default(x):
    print(x)
    time.sleep(10)
    return 2


def func_sleep_x_seconds(x):
    time.sleep(x)


def func_with_exception(x):
    time.sleep(10)
    raise Exception('1')


def function_with_results(x):
    time.sleep(10)
    return x
