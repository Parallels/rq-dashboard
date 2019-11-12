import json
import unittest

import redis
from rq import Worker, pop_connection, push_connection

from rq_dashboard.cli import make_flask_app

HTTP_OK = 200
HTTP_PERMANENT_REDIRECT = 308


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

    def test_queued_jobs_list(self):
        response_dashboard = self.client.get('/jobs/default/registries')
        self.assertEqual(response_dashboard.status_code, HTTP_OK)
        response_queued_redirect = self.client.get('/jobs/default/registries/queued')
        self.assertEqual(response_queued_redirect.status_code, HTTP_PERMANENT_REDIRECT)
        response = self.client.get('/jobs/default/registries/queued/1.json')
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.data.decode('utf8'))
        self.assertIsInstance(data, dict)
        self.assertIn('jobs', data)

    def test_registry_jobs_list(self):
        response_dashboard = self.client.get('/jobs/default/registries/failed')
        self.assertEqual(response_dashboard.status_code, HTTP_OK)
        response = self.client.get('/jobs/default/registries/failed/1.json')
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.data.decode('utf8'))
        self.assertIsInstance(data, dict)
        self.assertIn('jobs', data)

    def test_worker_python_version_field(self):
        w = Worker(['q'])
        w.register_birth()
        response = self.client.get('/workers.json')
        data = json.loads(response.data.decode('utf8'))
        if getattr(w, 'python_version', None):
            self.assertEqual(w.python_version, data['workers'][0]['python_version'])
        else:
            self.assertEqual('', data['workers'][0]['python_version'])
        w.register_death()

    def test_worker_version_field(self):
        w = Worker(['q'])
        w.register_birth()
        response = self.client.get('/workers.json')
        data = json.loads(response.data.decode('utf8'))
        if getattr(w, 'version', None):
            self.assertEqual(w.version, data['workers'][0]['version'])
        else:
            self.assertEqual('', data['workers'][0]['version'])
        w.register_death()


__all__ = [
    'BasicTestCase',
]
