from unittest import TestCase
from unittest.mock import Mock, patch

import requests

from medsenger_api import AgentApiClient, AgentApiRequestError
from medsenger_api.rest_client import RestApiClient


class TestAgentTokenRotation(TestCase):
    def setUp(self):
        self.client = RestApiClient('secret', host='https://medsenger.test')

    @patch('medsenger_api.rest_client.requests.post')
    def test_returns_inner_rotation_data(self, post):
        rotation_data = {
            'agent_token': 'new-token',
            'expires_in': 3600,
            'expires_at': '2026-07-28T13:00:00+03:00',
            'session_expires_at': '2026-07-28T20:00:00+03:00',
        }
        post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={'state': 'success', 'data': rotation_data}),
        )

        result = self.client.rotate_agent_token('current-token')

        self.assertEqual(result, rotation_data)
        post.assert_called_once_with(
            'https://medsenger.test/api/agents/access-token/rotate',
            json={'api_key': 'secret', 'agent_token': 'current-token'},
            timeout=30,
        )

    @patch('medsenger_api.rest_client.requests.post')
    def test_preserves_http_status_and_response_body(self, post):
        for status_code in (401, 403, 422):
            with self.subTest(status_code=status_code):
                body = {'state': 'error', 'error': 'rotation rejected'}
                post.return_value = Mock(
                    status_code=status_code,
                    json=Mock(return_value=body),
                )

                with self.assertRaises(AgentApiRequestError) as raised:
                    self.client.rotate_agent_token('current-token')

                self.assertEqual(raised.exception.status_code, status_code)
                self.assertEqual(raised.exception.response_body, body)

    @patch('medsenger_api.rest_client.requests.post')
    def test_preserves_non_json_error_body(self, post):
        response = Mock(status_code=500, text='upstream unavailable')
        response.json.side_effect = ValueError()
        post.return_value = response

        with self.assertRaises(AgentApiRequestError) as raised:
            self.client.rotate_agent_token('current-token')

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(raised.exception.response_body, 'upstream unavailable')

    @patch('medsenger_api.rest_client.requests.post')
    def test_wraps_transport_error(self, post):
        post.side_effect = requests.ConnectionError('connection refused')

        with self.assertRaises(AgentApiRequestError) as raised:
            self.client.rotate_agent_token('current-token')

        self.assertIsNone(raised.exception.status_code)
        self.assertIsNone(raised.exception.response_body)

    @patch.object(RestApiClient, 'rotate_agent_token')
    def test_agent_api_client_delegates_rotation(self, rotate):
        rotation_data = {'agent_token': 'new-token', 'expires_in': 3600}
        rotate.return_value = rotation_data
        client = AgentApiClient('secret', host='https://medsenger.test')

        result = client.rotate_agent_token('current-token')

        self.assertEqual(result, rotation_data)
        rotate.assert_called_once_with('current-token')

    @patch('medsenger_api.rest_client.requests.post')
    def test_rejects_malformed_success_response(self, post):
        body = {'state': 'success', 'data': {}}
        post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=body),
        )

        with self.assertRaises(AgentApiRequestError) as raised:
            self.client.rotate_agent_token('current-token')

        self.assertEqual(raised.exception.status_code, 200)
        self.assertEqual(raised.exception.response_body, body)
