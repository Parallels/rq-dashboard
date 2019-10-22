from __future__ import absolute_import

import json
import unittest

import redis
from rq import Queue, Worker, pop_connection, push_connection

from rq_dashboard.cli import make_flask_app

HTTP_OK = 200


class BasicTestCase(unittest.TestCase):
    redis_client = None

    def get_redis_client(self):
        if self.redis_client is None:
            self.redis_client = redis.Redis()
        return self.redis_client

    def setUp(self):
        self.app = make_flask_app(None, None, None, '')
        self.app.testing = True
        self.client = self.app.test_client()
        push_connection(self.get_redis_client())

    def tearDown(self):
        pop_connection()

    def test_dashboard_ok(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, HTTP_OK)

    def test_rq_instanses_list_json(self):
        response = self.client.get('/rq-instances.json')
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.data.decode('utf8'))
        self.assertIsInstance(data, dict)
        self.assertIn('rq_instances', data)

    def test_queues_list_json(self):
        response = self.client.get('/queues.json')
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.data.decode('utf8'))
        self.assertIsInstance(data, dict)
        self.assertIn('queues', data)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_workers_list_json(self):
        response = self.client.get('/workers.json')
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.data.decode('utf8'))
        self.assertIsInstance(data, dict)
        self.assertIn('workers', data)

    def test_failed_jobs(self):
        response = self.client.get('/failed')
        self.assertEqual(response.status_code, HTTP_OK)

    def test_worker_python_version_field(self):
        q = Queue()
        w = Worker([q], name='test_worker1')
        w.register_birth()
        response = self.client.get('/workers.json')
        data = json.loads(response.data.decode('utf8'))
        if getattr(w, 'python_version', None):
            self.assertEqual(w.python_version, data['workers'][0]['python_version'])
        else:
            self.assertEqual('', data['workers'][0]['python_version'])

    def test_worker_version_field(self):
        q = Queue()
        w = Worker([q], name='test_worker2')
        w.register_birth()
        response = self.client.get('/workers.json')
        data = json.loads(response.data.decode('utf8'))
        if getattr(w, 'version', None):
            self.assertEqual(w.version, data['workers'][0]['version'])
        else:
            self.assertEqual('', data['workers'][0]['version'])


__all__ = [
    'BasicTestCase',
]
