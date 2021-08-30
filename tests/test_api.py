from medsenger_api import AgentApiClient, prepare_file
from unittest import TestCase
from tests.config import *

class TestApi(TestCase):

    def create_client(self):
        return AgentApiClient(API_KEY, MAIN_HOST, AGENT_ID, True)

    def test_get_available_categories(self):
        print(self.create_client().get_available_categories(CONTRACT_ID))

    def test_get_records(self):
        print(self.create_client().get_records(CONTRACT_ID, "systolic_pressure"))

    def test_add_record_with_file(self):
        client = self.create_client()

        result = client.add_record(CONTRACT_ID, 'systolic_pressure', value=120, files=[prepare_file('test_api.py')])
        print(result)

    def test_get_file(self):
        client = self.create_client()

        result = client.get_file(CONTRACT_ID, 4)

        print(result)
