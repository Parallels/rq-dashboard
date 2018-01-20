from __future__ import absolute_import

import json
import unittest

from rq_dashboard.cli import make_flask_app

from .compatibility_mixin import CompatibilityMixin

HTTP_OK = 200


class BasicTestCase(unittest.TestCase, CompatibilityMixin):
    def setUp(self):
        self.app = make_flask_app(None, None, None, '')
        self.app.testing = True
        self.client = self.app.test_client()

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

    def test_workers_list_json(self):
        response = self.client.get('/workers.json')
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.data.decode('utf8'))
        self.assertIsInstance(data, dict)
        self.assertIn('workers', data)

__all__ = [
    'BasicTestCase',
]
