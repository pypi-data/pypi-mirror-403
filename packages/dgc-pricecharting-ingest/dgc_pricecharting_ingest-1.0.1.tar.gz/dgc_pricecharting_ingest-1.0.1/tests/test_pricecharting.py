# tests/test_pricecharting.py
import requests
import pytest

from dgc_pricecharting_ingest.pricecharting import product_exists  # adjust if your module has a different name


class _MockResponse:
    def __init__(self, status_code=200, json_data=None, json_raises=False):
        self.status_code = status_code
        self._json_data = json_data
        self._json_raises = json_raises

    def json(self):
        if self._json_raises:
            raise ValueError("Invalid JSON")
        return self._json_data


def test_product_exists_true(monkeypatch):
    """200 OK with a normal product JSON -> True"""
    mock_resp = _MockResponse(status_code=200, json_data={"id": 8314662, "name": "Example"})
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    assert product_exists(8314662) is True


def test_product_not_found_404(monkeypatch):
    """HTTP 404 -> False"""
    mock_resp = _MockResponse(status_code=404, json_data=None)
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    assert product_exists(9999999) is False


def test_product_not_found_json_error(monkeypatch):
    """200 with JSON {'status':'error','error':'No such product'} -> False"""
    mock_resp = _MockResponse(
        status_code=200,
        json_data={"status": "error", "error": "No such product"}
    )
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    assert product_exists(12345) is False


def test_product_not_found_json_error_alt_field(monkeypatch):
    """200 with JSON {'status':'error','error-message':'No such product'} -> False"""
    mock_resp = _MockResponse(
        status_code=200,
        json_data={"status": "error", "error-message": "No such product"}
    )
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    assert product_exists(12345) is False


def test_unknown_on_server_error(monkeypatch):
    """Non-200 and non-404 (500) -> None (unknown)"""
    mock_resp = _MockResponse(status_code=500, json_data=None)
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    assert product_exists(1) is None


def test_unknown_on_network_error(monkeypatch):
    """requests.get raises RequestException -> None"""
    def _raises(*a, **k):
        raise requests.RequestException("network error")
    monkeypatch.setattr(requests, "get", _raises)

    assert product_exists(1) is None


def test_unknown_on_invalid_json(monkeypatch):
    """200 but resp.json() raises ValueError -> None"""
    mock_resp = _MockResponse(status_code=200, json_data=None, json_raises=True)
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    assert product_exists(1) is None


def test_unknown_when_error_but_not_no_such_product(monkeypatch):
    """200 + status:error but error text is not 'No such product' -> None"""
    mock_resp = _MockResponse(
        status_code=200,
        json_data={"status": "error", "error": "Some other error happened"}
    )
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    assert product_exists(1) is None


def test_product_exists_with_non_dict_json(monkeypatch):
    """200 with JSON that's not a dict (e.g. list) -> treat as exists (True)"""
    mock_resp = _MockResponse(status_code=200, json_data=[1, 2, 3])
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    assert product_exists(42) is True


def test_product_exists_dict_without_status(monkeypatch):
    """200 with dict JSON but no 'status' field -> True (assume exists)"""
    mock_resp = _MockResponse(status_code=200, json_data={"id": 8314662, "name": "Example"})
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    assert product_exists(8314662) is True