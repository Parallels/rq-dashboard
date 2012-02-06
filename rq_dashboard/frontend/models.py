from rq import Queue, Worker


def all_queues():
    return Queue.all()

def all_workers():
    return Worker.all()
