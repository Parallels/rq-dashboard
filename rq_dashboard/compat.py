"""
Compatibility with rq 1.0, quick and dirty solution to support 1.0 without tons of changes in existing codebase.
"""

from rq.queue import Queue
from rq.job import Job
from rq.exceptions import NoSuchJobError


class FailedQueue(Queue):
    """
    Minimalist implementation of old failed queue.
    Very slow and memory-consuming.
    """
    def __init__(self, default_timeout=None, connection=None, async=True):
        super(FailedQueue, self).__init__(
            name=NotImplemented,
            default_timeout=default_timeout,
            connection=connection,
            async=async,
        )

        self._registries = (q.failed_job_registry for q in Queue.all())
        self._job_ids = None

    def get_job_ids(self, offset=0, length=-1):
        """
        Builds list of all failed jobs.

        Will be incredibly slow and memory-consuming in case of too many failed jobs,
        but leaving It this way for simplicity.
        """
        if self._job_ids is None:
            job_ids = []
            for registry in self._registries:
                job_ids.extend(registry.get_job_ids())
            self._job_ids = job_ids
        # Dirty hack to turn redis range to python list range
        start = offset
        if length >= 0:
            end = offset + length
        else:
            end = length
        if length == -1:
            return self._job_ids[start:]
        return self._job_ids[start:end]

    def fetch_job(self, job_id):
        try:
            return self.job_class.fetch(job_id, connection=self.connection)
        except NoSuchJobError:
            self.remove(job_id)

    def empty(self):
        for registry in self._registries:
            job_ids = registry.get_job_ids()
            for job_id in job_ids:
                job = Job.fetch(job_id)
                job.delete()

    def is_empty(self):
        return self.count == 0

    def compact(self):
        """
        Skipping implementation for failed queue
        """
        pass

    def __repr__(self):  # noqa
        return 'Queue(%r)' % (self.name,)

    def __str__(self):
        return '<Queue \'%s\'>' % (self.name,)

    @property
    def name(self):
        return 'failed'

    @name.setter
    def name(self, value):
        pass

    @property
    def count(self):
        return len(self.job_ids)


def get_failed_queue():
    return FailedQueue()


def get_all_queues():
    return Queue.all() + [FailedQueue()]
