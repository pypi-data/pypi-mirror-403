# tests/test_handlers.py
import sys
from types import ModuleType
import pytest

# -------------------------------
# FULL firebase_admin mock (must be installed BEFORE importing app.handlers)
# -------------------------------
mock_firebase_admin = ModuleType("firebase_admin")
mock_firebase_admin._apps = {}

# credentials submodule
mock_credentials = ModuleType("firebase_admin.credentials")
mock_credentials.Certificate = staticmethod(lambda x: "mock-cert")
mock_credentials.ApplicationDefault = staticmethod(lambda: "mock-application-default")

# storage submodule and bucket/blob mocks
mock_storage = ModuleType("firebase_admin.storage")

class _MockBlob:
    def __init__(self, path: str, bucket_name: str = "test-bucket"):
        self.path = path
        self._public = False
        self._uploaded = []  # store (data, content_type)
        self.bucket_name = bucket_name
        # Always provide public_url so app code can read it immediately
        self.public_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.path}"

    def upload_from_filename(self, filename, **kwargs):
        # simulate upload by recording filename
        self._uploaded.append(("filename", filename))
        return None

    def upload_from_string(self, data: bytes, **kwargs):
        # record bytes and content type if any
        content_type = kwargs.get("content_type") or kwargs.get("contentType") or kwargs.get("content-type")
        self._uploaded.append(("string", data, content_type))
        return None

    def make_public(self):
        self._public = True
        return None

    def __repr__(self):
        return f"<_MockBlob path={self.path} public={self._public}>"

class _MockBucket:
    def __init__(self, name: str = "test-bucket"):
        self.name = name

    def blob(self, path: str):
        return _MockBlob(path, bucket_name=self.name)

def _mock_bucket(name: str | None = None):
    return _MockBucket(name or "test-bucket")

mock_storage.bucket = _mock_bucket

# Wire up firebase_admin module
mock_firebase_admin.credentials = mock_credentials
mock_firebase_admin.storage = mock_storage
mock_firebase_admin.initialize_app = lambda *args, **kwargs: None

# Register mocks into sys.modules before importing the app
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.credentials"] = mock_credentials
sys.modules["firebase_admin.storage"] = mock_storage

# -------------------------------
# Now import the app module (module under test)
# -------------------------------
import dgc_pricecharting_ingest.handlers as app_module

# -------------------------------
# Fixtures and helpers
# -------------------------------

@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


class MockResponse:
    def __init__(self, text: str, status_code: int = 200, headers: dict | None = None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "image/jpeg"}

# Helper to patch common behavior in many tests
def _patch_basic_success(monkeypatch, *, uploads_any_success=True, mark_raises=False):
    """
    Patches:
      - verify_request -> True
      - pricecharting_url -> returns product_name
      - extract_pricecharting_id -> returns part after '-' in product_name
      - extract_image_info -> returns {"image_id": f"img-{html}", "no_image": False}
      - requests.get -> MockResponse(url, 200) (accepts *args, **kwargs)
      - download_and_upload_images -> returns a tuple (results_list, stored_image_id)
      - mark_card_uploaded -> spy (may raise if mark_raises True)
    Returns: calls list for mark_card_uploaded
    """
    monkeypatch.setattr(app_module, "verify_request", lambda req, sa, aud: True)
    monkeypatch.setattr(app_module, "pricecharting_url", lambda console, product: product)

    def extract_pid(html: str):
        if isinstance(html, str) and "-" in html:
            return html.split("-", 1)[1]
        return None

    monkeypatch.setattr(app_module, "extract_pricecharting_id", extract_pid)

    monkeypatch.setattr(
        app_module,
        "extract_image_info",
        lambda html: {"image_id": f"img-{html}", "no_image": False},
    )

    # Robust requests.get mock that accepts any kwargs
    def mock_requests_get(url, *args, **kwargs):
        return MockResponse(url, 200)

    monkeypatch.setattr(app_module.requests, "get", mock_requests_get)

    # NEW: return a tuple (results_list, stored_image_id)
    def download_and_upload_images(_id, card_id, image_id):
        if uploads_any_success:
            results = [(f"src-{card_id}-1", f"dest-{card_id}-1"), (f"src-{card_id}-2", None)]
            stored_id = f"stored-{card_id}"
            return results, stored_id
        else:
            results = [(f"src-{card_id}-1", None), (f"src-{card_id}-2", None)]
            stored_id = None
            return results, stored_id

    monkeypatch.setattr(app_module, "download_and_upload_images", download_and_upload_images)

    calls = []
    def mark_card_uploaded(card_id, image_id):
        calls.append((card_id, image_id))
        if mark_raises:
            raise RuntimeError("db error")
    monkeypatch.setattr(app_module, "mark_card_uploaded", mark_card_uploaded)

    # patch other DB marking helpers so tests don't hit DB
    monkeypatch.setattr(app_module, "mark_card_noimage", lambda i: None)
    monkeypatch.setattr(app_module, "mark_card_invalid_url", lambda i: None)
    monkeypatch.setattr(app_module, "mark_card_deleted", lambda i: None)
    monkeypatch.setattr(app_module, "update_card_number", lambda cid, n: None)

    return calls

# -------------------------------
# Tests
# -------------------------------

def test_unauthorized(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_request", lambda req, sa, aud: False)
    resp = client.post("/", json={"_id": "x", "id": 1, "console_name": "X", "product_name": "pid-1"})
    assert resp.status_code == 403
    assert resp.get_json() == {"error": "Unauthorized"}

def test_non_json_body(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_request", lambda req, sa, aud: True)
    resp = client.post("/", data="not-json", content_type="text/plain")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Request must be JSON"}

def test_single_item_success(monkeypatch, client):
    calls = _patch_basic_success(monkeypatch, uploads_any_success=True)

    payload = {
        "_id": "abc",
        "id": 123,
        "console_name": "NES",
        "product_name": "pid-123",
    }

    resp = client.post("/", json=payload)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["processed"] == 1
    assert body["uploaded"] == 1
    assert body["skipped"] == 0
    assert body["failed"] == 0
    detail = body["details"][0]
    assert detail["id"] == 123
    assert detail["status"] == "uploaded"
    assert calls == [(123, 'stored-123')]

def test_batch_mixed_outcomes(monkeypatch, client):
    _patch_basic_success(monkeypatch, uploads_any_success=True)

    # Override download/upload to simulate per-id outcomes
    def download_and_upload_images_by_id(_id, card_id, image_id):
        if card_id == 1:
            return ([(f"src-{card_id}-1", f"dest-{card_id}-1")], f"stored-{card_id}")
        if card_id == 3:
            return ([(f"src-{card_id}-1", None)], f"stored-{card_id}")
        return ([], None)

    monkeypatch.setattr(app_module, "download_and_upload_images", download_and_upload_images_by_id)
    monkeypatch.setattr(app_module, "pricecharting_url", lambda console, product: product)

    # Robust requests.get mock that accepts params and other kwargs used by product_exists
    def requests_get_accept_kwargs(url, *args, **kwargs):
        return MockResponse(url, 200)

    monkeypatch.setattr(app_module.requests, "get", requests_get_accept_kwargs)
    monkeypatch.setattr(app_module, "extract_pricecharting_id", lambda html: html.split("-",1)[1] if "-" in html else None)
    monkeypatch.setattr(app_module, "extract_image_info", lambda html: {"image_id": f"img-{html}", "no_image": False})

    # ensure product_exists returns False so PID mismatch path becomes 'skipped'
    monkeypatch.setattr(app_module, "product_exists", lambda _card_id: False)

    batch = [
        {"_id": "a", "id": 1, "console_name": "X", "product_name": "pid-1"},
        {"_id": "b", "id": 2, "console_name": "X", "product_name": "pid-999"},
        {"_id": "c", "id": 3, "console_name": "X", "product_name": "pid-3"},
    ]

    resp = client.post("/", json=batch)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["processed"] == 3
    # now we expect: one uploaded, one skipped (pid mismatch), one failed (uploads failed)
    assert body["uploaded"] == 1
    assert body["skipped"] == 1
    assert body["failed"] == 1
    statuses = [d["status"] for d in body["details"]]
    assert statuses == ["uploaded", "skipped", "failed"]
    uploaded_detail = body["details"][0]
    assert all(dest is not None for _, dest in uploaded_detail["uploads"])

def test_mark_card_uploaded_raises_marks_failed(monkeypatch, client):
    calls = _patch_basic_success(monkeypatch, uploads_any_success=True, mark_raises=True)

    payload = {
        "_id": "abc123",
        "id": 42,
        "console_name": "NES",
        "product_name": "pid-42",
    }

    resp = client.post("/", json=payload)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["processed"] == 1
    assert body["uploaded"] == 0
    assert body["failed"] == 1
    detail = body["details"][0]
    assert detail["status"] == "failed"
    assert "mark_card_uploaded error" in (detail.get("reason") or "")
