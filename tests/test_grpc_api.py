import time

from medsenger_api import AgentApiClient, prepare_file
from unittest import TestCase
from tests.config import *


class TestApi(TestCase):
    grpc_client = AgentApiClient(API_KEY, MAIN_HOST, AGENT_ID, True, True, 'localhost')
    default_client = AgentApiClient(API_KEY, MAIN_HOST, AGENT_ID, True, False)

    def test_get_categories(self):
        assert self.grpc_client.get_categories() == self.default_client.get_categories()

    def test_get_available_categories(self):
        G = self.grpc_client.get_available_categories(CONTRACT_ID)
        D = self.default_client.get_available_categories(CONTRACT_ID)

        G.sort(key=lambda c: c['id'])
        D.sort(key=lambda c: c['id'])

        for a, b in zip(G, D):
            if a != b:
                print("a: ", a)
                print("b: ", b)

        assert G == D



    def test_get_records(self):

        S = time.time()
        G = self.grpc_client.get_records(CONTRACT_ID, "systolic_pressure")
        print("G time:", time.time() - S)

        S = time.time()
        D = self.default_client.get_records(CONTRACT_ID, "systolic_pressure")
        print("D time:", time.time() - S)

        G['values'].sort(key=lambda c: c['id'])
        D['values'].sort(key=lambda c: c['id'])

        for a, b in zip(G['values'], D['values']):
            if a != b:
                print("a: ", a)
                print("b: ", b)

        assert G == D

    def test_get_records_from_multiple_categroies(self):
        S = time.time()
        G = self.grpc_client.get_records(CONTRACT_ID, "systolic_pressure,diastolic_pressure,pulse")
        print("G time:", time.time() - S)

        S = time.time()
        D = self.default_client.get_records(CONTRACT_ID, "systolic_pressure,diastolic_pressure,pulse")
        print("D time:", time.time() - S)

        G.sort(key=lambda c: c['id'])
        D.sort(key=lambda c: c['id'])

        print(type(G), type(D))

        for a, b in zip(G, D):
            if a != b:
                print("a: ", a)
                print("b: ", b)

        assert G == D

    def test_get_records_from_multiple_categroies_with_offset(self):
        S = time.time()
        G = self.grpc_client.get_records(CONTRACT_ID, "systolic_pressure,diastolic_pressure,pulse", offset=100, limit=100)
        print("G time:", time.time() - S)

        S = time.time()
        D = self.default_client.get_records(CONTRACT_ID, "systolic_pressure,diastolic_pressure,pulse", offset=100, limit=100)
        print("D time:", time.time() - S)

        G.sort(key=lambda c: c['id'])
        D.sort(key=lambda c: c['id'])

        print(type(G), type(D))

        for a, b in zip(G, D):
            if a != b:
                print("a: ", a)
                print("b: ", b)

        assert G == D

    def test_get_records_from_multiple_categroies_with_time(self):
        T = int(time.time() - 2 * 30 * 24 * 60 * 60)
        F = int(time.time() - 3 * 30 * 24 * 60 * 60)

        S = time.time()
        G = self.grpc_client.get_records(CONTRACT_ID, "systolic_pressure,diastolic_pressure,pulse", time_from=F, time_to=T)
        print("G time:", time.time() - S)

        S = time.time()
        D = self.default_client.get_records(CONTRACT_ID, "systolic_pressure,diastolic_pressure,pulse", time_from=F, time_to=T)
        print("D time:", time.time() - S)

        if D and G:
            G.sort(key=lambda c: c['id'])
            D.sort(key=lambda c: c['id'])
        else:
            print(D,G)

        print(type(G), type(D))

        if D and G:
            for a, b in zip(G, D):
                if a != b:
                    print("a: ", a)
                    print("b: ", b)

        assert G == D
