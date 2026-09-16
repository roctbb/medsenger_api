from unittest import TestCase
from unittest.mock import Mock, patch

from medsenger_api import AgentApiClient


class TestAttachmentDownloads(TestCase):
    def setUp(self):
        self.client = AgentApiClient('test-key', host='https://medsenger.test')

    @patch('medsenger_api.rest_client.requests.post')
    def test_image_methods_send_image_id(self, post):
        response = {'state': 'ok', 'base64': 'aW1hZ2U='}
        post.return_value = Mock(status_code=200, json=Mock(return_value=response))

        for method in ('get_image', 'download_image'):
            for size in ('real', 'small', 'thumb'):
                with self.subTest(method=method, size=size):
                    post.reset_mock()

                    result = getattr(self.client, method)(123, size)

                    self.assertEqual(result, response)
                    post.assert_called_once_with(
                        'https://medsenger.test/api/agents/image',
                        json={'api_key': 'test-key', 'image_id': 123, 'size': size},
                    )

    @patch('medsenger_api.rest_client.requests.post')
    def test_attachment_methods_keep_attachment_id(self, post):
        response = {'state': 'ok', 'base64': 'ZmlsZQ=='}
        post.return_value = Mock(status_code=200, json=Mock(return_value=response))

        for method in ('get_attachment', 'download_attachment'):
            with self.subTest(method=method):
                post.reset_mock()

                result = getattr(self.client, method)(456)

                self.assertEqual(result, response)
                post.assert_called_once_with(
                    'https://medsenger.test/api/agents/attachment',
                    json={'api_key': 'test-key', 'attachment_id': 456},
                )
