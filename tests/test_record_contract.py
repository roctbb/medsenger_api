from unittest import TestCase
from unittest.mock import Mock, patch

from medsenger_api import AgentApiClient
from medsenger_api.grpc_client import RecordsClient
from medsenger_api.rest_client import RestApiClient
from medsenger_api.protocol import records_pb2 as pb2


class RecordContractTest(TestCase):
    @patch('medsenger_api.rest_client.requests.post')
    def test_rest_filter_and_legacy_requests(self, post):
        post.return_value = Mock(status_code=200, json=Mock(return_value=[]))
        client = RestApiClient('key', host='https://medsenger.test')
        client.get_records(10, 'pulse')
        self.assertNotIn('record_contract_id', post.call_args.kwargs['json'])
        for category in ('pulse', 'pulse,weight', None):
            client.get_records(10, category, record_contract_id=10, return_count=True)
            self.assertEqual(post.call_args.kwargs['json']['record_contract_id'], 10)
            self.assertEqual(post.call_args.kwargs['json']['contract_id'], 10)
        client.get_records(user_id=1, record_contract_id=20)
        self.assertEqual(post.call_args.kwargs['json']['user_id'], 1)
        self.assertNotIn('contract_id', post.call_args.kwargs['json'])
        client.get_available_categories(10, record_contract_id=10)
        self.assertEqual(post.call_args.kwargs['json']['record_contract_id'], 10)

    def client(self):
        client = AgentApiClient('key', host='https://medsenger.test')
        client.user_cache[10] = 1
        client.grpc_client = Mock()
        client.rest_client = Mock()
        return client

    def test_wrapper_passes_filter_to_grpc_and_rest_fallback(self):
        client = self.client()
        client.get_records(10, 'pulse', record_contract_id=10)
        self.assertEqual(client.grpc_client.get_records.call_args.kwargs['record_contract_id'], 10)
        self.assertEqual(client.grpc_client.get_records.call_args.kwargs['user_id'], 1)
        client.grpc_client.get_records.side_effect = RuntimeError('simulated unavailable gRPC')
        client.get_records(10, 'pulse', record_contract_id=10)
        self.assertEqual(client.rest_client.get_records.call_args.kwargs['record_contract_id'], 10)
        client.grpc_client.count_records.side_effect = RuntimeError('simulated unavailable gRPC')
        client.get_records(10, 'pulse', record_contract_id=10, return_count=True)
        self.assertEqual(client.rest_client.get_records.call_args.kwargs['record_contract_id'], 10)

    def test_batch_preserves_each_filter_including_fallback(self):
        client = self.client()
        queries = [dict(contract_id=10, category_name='pulse', record_contract_id=10),
                   dict(user_id=1, category_name='pulse', record_contract_id=20)]
        client.get_multiple_records(queries)
        self.assertEqual([q['record_contract_id'] for q in client.grpc_client.get_multiple_records.call_args.args[0]], [10, 20])
        client.grpc_client.get_multiple_records.side_effect = RuntimeError('batch unavailable')
        client.grpc_client.get_records.side_effect = RuntimeError('unavailable')
        client.get_multiple_records(queries)
        self.assertEqual([call.kwargs['record_contract_id'] for call in client.rest_client.get_records.call_args_list], [10, 20])

    def test_category_filter_survives_fallback(self):
        client = self.client()
        client.grpc_client.get_categories_for_user.side_effect = RuntimeError('unavailable')
        client.rest_client.get_available_categories.return_value = []
        client.get_available_categories(10, record_contract_id=10)
        self.assertEqual(client.grpc_client.get_categories_for_user.call_args.kwargs['record_contract_id'], 10)
        self.assertEqual(client.rest_client.get_available_categories.call_args.kwargs['record_contract_id'], 10)

    def test_grpc_serialization_and_record_presentation(self):
        client = RecordsClient(api_key='key')
        category = pb2.Category(id=1, name='pulse', type='integer', locale='ru')
        client._RecordsClient__categories_by_id = {1: [category]}
        client._RecordsClient__categories_by_name = {'pulse': [category]}
        legacy = pb2.Record(id=1, category_id=1, value='60', params='null', additions='null')
        scoped = pb2.Record(id=2, category_id=1, value='61', params='null', additions='null', contract_id=10)
        self.assertIsNone(client._RecordsClient__present_record(legacy)['contract_id'])
        self.assertEqual(client._RecordsClient__present_record(scoped)['contract_id'], 10)
        with patch.object(client, '_RecordsClient__make_request', return_value=pb2.RecordList(records=[scoped], count=1)) as call:
            client.get_records(1, 'pulse', record_contract_id=10)
            self.assertEqual(call.call_args.args[1].record_contract_id, 10)
            client.count_records(1, 'pulse', record_contract_id=10)
            self.assertEqual(call.call_args.args[0], 'CountRecords')
            self.assertEqual(call.call_args.args[1].record_contract_id, 10)
            client.get_records(1, None)
            self.assertFalse(call.call_args.args[1].HasField('record_contract_id'))
        with patch.object(client, '_RecordsClient__make_request', return_value=pb2.MultiRecordAnswer(answers=[pb2.RecordList(), pb2.RecordList()])) as call:
            client.get_multiple_records([
                dict(user_id=1, category_name='pulse', time_from=None, time_to=None, offset=None, limit=None, group=False, record_contract_id=10),
                dict(user_id=1, category_name='pulse', time_from=None, time_to=None, offset=None, limit=None, group=False, record_contract_id=20),
            ])
            self.assertEqual([q.record_contract_id for q in call.call_args.args[1].queries], [10, 20])

    @patch('medsenger_api.rest_client.requests.post')
    def test_existing_write_methods_already_send_contract(self, post):
        post.return_value = Mock(status_code=200, json=Mock(return_value='OK'))
        client = RestApiClient('key', host='https://medsenger.test')
        client.add_record(10, 'pulse', 60)
        self.assertEqual(post.call_args.kwargs['json']['contract_id'], 10)
        client.add_records(20, [('pulse', 60), ('pulse', 61)])
        self.assertEqual(post.call_args.kwargs['json']['contract_id'], 20)
        self.assertEqual(len(post.call_args.kwargs['json']['values']), 2)
