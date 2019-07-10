from redis import Redis
from rq import Queue

from dev_scripts import functions


default = Queue('default', connection=Redis(db=0, host='127.0.0.1'))
fast = Queue('fast', connection=Redis(db=0, host='127.0.0.1'))
new = Queue('new', connection=Redis(db=0, host='127.0.0.1'))


def create_n_jobs_on_queue(n, queue, fn):
    for index in range(n):
        queue.enqueue(fn, index, ttl=3600, result_ttl=3600)


# create_n_jobs_on_queue(10, default, functions.func_default)
create_n_jobs_on_queue(10, new, functions.func_default)
# create_n_jobs_on_queue(10, new, functions.func_with_exception)
# create_n_jobs_on_queue(100, fast, functions.func_with_exception)
# create_n_jobs_on_queue(100, fast, functions.function_with_results)
