import unittest
from unittest.mock import Mock, patch
import requests
from medsenger_api import AgentApiClient
from medsenger_api.utils import AgentApiRequestError


class CacheTransportTest(unittest.TestCase):
    @patch('medsenger_api.rest_client.requests.post')
    def test_existing_protocol_and_plain_text_acknowledgment(self, post):
        post.return_value = Mock(
            status_code=200, text='ok', json=Mock(side_effect=ValueError)
        )
        client = AgentApiClient('key', host='https://medsenger.example.test')
        self.assertEqual(client.update_cache_strict(42), 'ok')
        post.assert_called_once_with(
            'https://medsenger.example.test/api/agents/cache',
            json={'api_key': 'key', 'contract_id': 42},
            timeout=30,
        )

    @patch('medsenger_api.rest_client.requests.post')
    def test_failed_delivery_is_visible_to_the_outbox(self, post):
        client = AgentApiClient('key', host='https://medsenger.example.test')
        post.side_effect = requests.Timeout('offline')
        with self.assertRaises(AgentApiRequestError):
            client.update_cache_strict(42)
        post.side_effect = None
        post.return_value = Mock(
            status_code=503, text='unavailable', json=Mock(side_effect=ValueError)
        )
        with self.assertRaises(AgentApiRequestError):
            client.update_cache_strict(42)
