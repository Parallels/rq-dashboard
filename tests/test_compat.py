from __future__ import absolute_import

import json
import unittest

import redis
from rq import pop_connection, push_connection
from rq import version as rq_version

from rq_dashboard.cli import make_flask_app
from rq_dashboard.compat import get_all_queues

from .fixtures.rq_1_0 import fxt_all_failed, fxt_ready

HTTP_OK = 200


class CompatTestCase(unittest.TestCase):
    redis_client = None

    def get_redis_client(self):
        if self.redis_client is None:
            self.redis_client = redis.Redis()
        return self.redis_client

    def setup_fixtures(self, fixtures):
        r = self.get_redis_client()
        for fxt in fixtures:
            name, ttl, value = fxt
            r.restore(name=name, ttl=ttl, value=value, replace=True)

    def setUp(self):
        if not rq_version.VERSION.startswith('1.'):
            self.skipTest('Skipping 1.x tests, because running with %s' % rq_version.VERSION)

        self.app = make_flask_app(None, None, None, '')
        self.app.testing = True
        self.client = self.app.test_client()

        self.get_redis_client().flushdb()
        push_connection(self.get_redis_client())

    def tearDown(self):
        pop_connection()
        self.get_redis_client().flushdb()

    def assertItems(self, expected, actual):
        self.assertEqual(sorted(expected), sorted(actual))

    def test_all_queues_empty(self):
        queues = get_all_queues()
        names = [q.name for q in queues]
        self.assertItems(('failed',), names)

    def test_all_queues(self):
        self.setup_fixtures(fxt_ready)
        queues = get_all_queues()
        names = [q.name for q in queues]
        self.assertItems(('high', 'medium', 'low', 'failed'), names)

    def test_failed_jobs(self):
        self.setup_fixtures(fxt_all_failed)
        response = self.client.get('/jobs/failed/1.json')
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.data.decode('utf8'))
        self.assertItems(('jobs', 'name', 'pagination'), data.keys())
        self.assertEqual(data['name'], 'failed')
        self.assertEqual(len(data['jobs']), 5)
        jobs = data['jobs']

        response = self.client.get('/jobs/failed/2.json')
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.data.decode('utf8'))
        self.assertItems(('jobs', 'name', 'pagination'), data.keys())
        self.assertEqual(data['name'], 'failed')
        self.assertEqual(len(data['jobs']), 4)
        jobs += data['jobs']

        # Making sure that jobs are sorted by creation date, not by origin queue
        creation_dates = [j['created_at'] for j in jobs]
        self.assertEqual(sorted(creation_dates), creation_dates)

        # Checking that original queue names are correct
        queue_names = [j['origin'] for j in jobs]
        self.assertEqual(queue_names, ['low', 'medium', 'high'] * 3)


__all__ = [
    'CompatTestCase',
]
