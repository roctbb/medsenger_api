from unittest import TestCase
from unittest.mock import Mock, patch

from medsenger_api import AgentApiClient
from medsenger_api.rest_client import RestApiClient


class TestComplianceEvents(TestCase):
    def setUp(self):
        self.client = RestApiClient('secret', host='https://medsenger.test')

    @patch('medsenger_api.rest_client.requests.post')
    def test_creates_event(self, post):
        response = {'state': 'ok', 'created': True, 'event': {'id': 7}}
        post.return_value = Mock(status_code=200, json=Mock(return_value=response))

        result = self.client.create_compliance_event(12, 'action-request:42', 'form_9')

        self.assertEqual(result, response)
        post.assert_called_once_with(
            'https://medsenger.test/api/agents/compliance/events',
            json={
                'api_key': 'secret',
                'contract_id': 12,
                'external_id': 'action-request:42',
                'code': 'form_9',
            },
            timeout=30,
        )

    @patch('medsenger_api.rest_client.requests.post')
    def test_completes_event_by_id(self, post):
        post.return_value = Mock(status_code=200, json=Mock(return_value={'state': 'ok'}))

        self.client.complete_compliance_event(12, event_id=7)

        post.assert_called_once_with(
            'https://medsenger.test/api/agents/compliance/events/complete',
            json={'api_key': 'secret', 'contract_id': 12, 'id': 7},
            timeout=30,
        )

    @patch('medsenger_api.rest_client.requests.post')
    def test_cancels_event_by_external_id(self, post):
        post.return_value = Mock(status_code=200, json=Mock(return_value={'state': 'ok'}))

        self.client.cancel_compliance_event(12, external_id='action-request:42')

        post.assert_called_once_with(
            'https://medsenger.test/api/agents/compliance/events/cancel',
            json={
                'api_key': 'secret',
                'contract_id': 12,
                'external_id': 'action-request:42',
            },
            timeout=30,
        )

    @patch('medsenger_api.rest_client.requests.post')
    def test_gets_events_by_user(self, post):
        response = {'state': 'ok', 'events': [], 'total': 0, 'limit': 25, 'offset': 5}
        post.return_value = Mock(status_code=200, json=Mock(return_value=response))

        result = self.client.get_compliance_events(
            '2026-08-01',
            '2026-08-17',
            user_id=22,
            limit=25,
            offset=5,
        )

        self.assertEqual(result, response)
        post.assert_called_once_with(
            'https://medsenger.test/api/agents/compliance/events/get',
            json={
                'api_key': 'secret',
                'date_from': '2026-08-01',
                'date_to': '2026-08-17',
                'user_id': 22,
                'limit': 25,
                'offset': 5,
            },
            timeout=30,
        )

    def test_rejects_ambiguous_selectors(self):
        with self.assertRaises(ValueError):
            self.client.complete_compliance_event(12)
        with self.assertRaises(ValueError):
            self.client.complete_compliance_event(12, event_id=7, external_id='event:7')
        with self.assertRaises(ValueError):
            self.client.get_compliance_events('2026-08-01', '2026-08-17')
        with self.assertRaises(ValueError):
            self.client.get_compliance_events(
                '2026-08-01',
                '2026-08-17',
                contract_id=12,
                user_id=22,
            )

    @patch.object(RestApiClient, 'get_compliance_events')
    def test_agent_api_client_delegates_list_request(self, get_events):
        get_events.return_value = {'events': []}
        client = AgentApiClient('secret', host='https://medsenger.test')

        result = client.get_compliance_events(
            '2026-08-01',
            '2026-08-17',
            contract_id=12,
            limit=10,
        )

        self.assertEqual(result, {'events': []})
        get_events.assert_called_once_with(
            '2026-08-01',
            '2026-08-17',
            contract_id=12,
            user_id=None,
            limit=10,
            offset=None,
        )
