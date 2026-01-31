import pytest, requests
from etiket_client.remote.client import client

@pytest.fixture(params=[
    (requests.exceptions.ConnectionError, "Connection lost"),
    (requests.exceptions.HTTPError, "Service not available")
], ids=["connection_loss", "service_unavailable"])
def simulated_error(monkeypatch, request):
    exception_cls, error_message = request.param
    def fake_get(*args, **kwargs):
        print("raising exception:", exception_cls)
        raise exception_cls(error_message)
    monkeypatch.setattr(client, "get", fake_get)
    monkeypatch.setattr(client, "post", fake_get)
    monkeypatch.setattr(client, "put", fake_get)
    monkeypatch.setattr(client, "delete", fake_get)
    monkeypatch.setattr(client, "patch", fake_get)
    
    return error_message