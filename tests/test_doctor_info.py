from unittest import TestCase
from unittest.mock import Mock, patch

from medsenger_api import AgentApiClient


class DoctorInfoTest(TestCase):
    @patch('medsenger_api.rest_client.requests.post')
    def test_current_and_all_methods_use_distinct_routes_and_preserve_responses(self, post):
        client = AgentApiClient('test-key', host='https://medsenger.test')
        response = {
            'state': 'success',
            'doctor': {'id': 42},
            'contracts': [{'contract_id': 123, 'active': False}],
            'doctor_contracts': {'42': [123]},
        }
        post.return_value = Mock(status_code=200, json=Mock(return_value=response))

        for method, path in (
            (client.get_doctor_info, '/doctor/info'),
            (client.get_all_doctor_info, '/doctor/info/all'),
        ):
            with self.subTest(path=path):
                post.reset_mock()
                self.assertEqual(response, method(42))
                post.assert_called_once_with(
                    'https://medsenger.test/api/agents' + path,
                    json={'api_key': 'test-key', 'doctor_id': 42},
                )

    @patch('medsenger_api.rest_client.requests.post')
    def test_unavailable_all_endpoint_returns_an_error_instead_of_falling_back_to_current(self, post):
        post.return_value = Mock(status_code=404)
        client = AgentApiClient('test-key', host='https://medsenger.test')

        self.assertEqual({
            'state': 'error', 'doctor': None, 'contracts': [], 'doctor_contracts': {},
        }, client.get_all_doctor_info(42))
        self.assertEqual(1, post.call_count)
