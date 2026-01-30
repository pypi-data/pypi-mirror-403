# tests/test_img.py
import sys
from types import ModuleType
import importlib
import pytest

# ---------------------------
# Build a full firebase_admin mock BEFORE importing app.img
# ---------------------------
mock_firebase_admin = ModuleType("firebase_admin")
mock_firebase_admin._apps = {}

# credentials
mock_credentials = ModuleType("firebase_admin.credentials")
mock_credentials.ApplicationDefault = staticmethod(lambda: "mock-app-default")
mock_credentials.Certificate = staticmethod(lambda x: "mock-cert")
mock_firebase_admin.credentials = mock_credentials

# storage (we will set bucket to return our DummyBucket below)
mock_storage = ModuleType("firebase_admin.storage")
mock_firebase_admin.storage = mock_storage

mock_firebase_admin.initialize_app = lambda *a, **k: None

# register modules so `from firebase_admin import credentials, storage, initialize_app` works
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.credentials"] = mock_credentials
sys.modules["firebase_admin.storage"] = mock_storage

# ---------------------------
# DummyBucket / DummyBlob definitions (used by mock storage.bucket)
# ---------------------------
class DummyBlob:
    def __init__(self, name: str, store: list, fail_on_upload: bool = False):
        self.name = name
        self._store = store
        self._fail_on_upload = fail_on_upload
        self._is_public = False
        # Always have public_url attribute (tests / code may access it immediately)
        self.public_url = f"https://storage.googleapis.com/dummy-bucket/{self.name}"

    def upload_from_string(self, data: bytes, content_type: str = None):
        if self._fail_on_upload:
            raise RuntimeError("upload failed")
        self._store.append((self.name, data, content_type))

    def make_public(self):
        # mark as public; public_url remains available
        self._is_public = True

    def __repr__(self):
        return f"<DummyBlob {self.name} public={self._is_public}>"


class DummyBucket:
    def __init__(self, name: str = "dummy-bucket", fail_on_prefixes: list[str] | None = None):
        self.name = name
        self._store: list[tuple] = []
        self._fail_on_prefixes = set(fail_on_prefixes or [])

    def blob(self, path: str) -> DummyBlob:
        should_fail = any(path.startswith(p) for p in self._fail_on_prefixes)
        return DummyBlob(path, self._store, fail_on_upload=should_fail)

    def get_store(self):
        return list(self._store)

# Make storage.bucket return a DummyBucket factory (fresh instance when called)
def _bucket_factory(name: str | None = None):
    return DummyBucket(name or "dummy-bucket")

mock_storage.bucket = _bucket_factory

# ---------------------------
# Now import module under test (after mocks are installed)
# ---------------------------
# importlib ensures we load fresh module after injecting mocks
app_img = importlib.import_module("dgc_pricecharting_ingest.img")

# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture(autouse=True)
def reset_bucket():
    # Replace app_img.bucket with a new DummyBucket for each test to isolate state.
    app_img.bucket = DummyBucket(name="dummy-bucket")
    yield
    # cleanup if needed
    app_img.bucket = DummyBucket(name="dummy-bucket")

class MockResp:
    def __init__(self, content: bytes, status_code: int = 200, headers: dict | None = None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "image/jpeg"}

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            # mimic requests.raise_for_status() behavior
            raise Exception(f"{self.status_code} error")

# ---------------------------
# Tests
# ---------------------------
def test_download_image_success(monkeypatch):
    monkeypatch.setattr(app_img.requests, "get", lambda url, timeout=10: MockResp(b"imagedata", 200, {"Content-Type": "image/jpeg"}))
    data, ctype = app_img.download_image("https://example.com/1.jpg")
    assert data == b"imagedata"
    assert ctype == "image/jpeg"

def test_download_image_failure(monkeypatch):
    def bad_get(url, timeout=10):
        raise RuntimeError("net error")
    monkeypatch.setattr(app_img.requests, "get", bad_get)
    data, ctype = app_img.download_image("https://example.com/404.jpg")
    assert data is None and ctype is None

def test_upload_image_success(monkeypatch):
    # ensure bucket is DummyBucket from fixture
    bucket = app_img.bucket
    assert isinstance(bucket, DummyBucket)

    public_url = app_img.upload_image(b"abc", "image/jpeg", "pricecharting/123/tiny.jpg")
    assert public_url == f"https://storage.googleapis.com/{bucket.name}/pricecharting/123/tiny.jpg"
    assert ("pricecharting/123/tiny.jpg", b"abc", "image/jpeg") in bucket.get_store()

def test_download_and_upload_images_success(monkeypatch):
    # make generate_uuid deterministic
    monkeypatch.setattr(app_img, "generate_uuid", lambda _id: f"{_id}-uid")
    updates = []
    monkeypatch.setattr(app_img, "update_image_path", lambda pid, name, url: updates.append((pid, name, url)))

    # requests.get returns image bytes
    def good_get(url, timeout=10):
        return MockResp(b"imgbytes-" + url.encode("utf-8"), 200, {"Content-Type": "image/jpeg"})
    monkeypatch.setattr(app_img.requests, "get", good_get)

    results, uid = app_img.download_and_upload_images("42", 1001, "img-abc123")
    assert len(results) == 3
    for src_url, uploaded_url in results:
        assert src_url.startswith("https://storage.googleapis.com/images.pricecharting.com/")
        assert uploaded_url is not None
    assert len(updates) == 3
    # ensure update_image_path entries are for the expected names
    assert set(n for _, n, _ in updates) <= {"tiny", "small", "normal"}
    assert uid == "42-uid"

def test_download_and_upload_images_partial_download_failure(monkeypatch):
    # fail download for 240.jpg
    def selective_get(url, timeout=10):
        if url.endswith("/240.jpg"):
            raise RuntimeError("fetch failed")
        return MockResp(b"good", 200, {"Content-Type": "image/jpeg"})
    monkeypatch.setattr(app_img.requests, "get", selective_get)

    monkeypatch.setattr(app_img, "generate_uuid", lambda i: "uid-1")
    called = []
    monkeypatch.setattr(app_img, "update_image_path", lambda pid, name, url: called.append((pid, name, url)))

    results, uid = app_img.download_and_upload_images("77", 2002, "img-zzz")
    # middle size (240) should be (url, None)
    assert any(src.endswith("/240.jpg") and uploaded is None for src, uploaded in results)
    # update_image_path called only for successful uploads (2)
    assert len(called) == 2
    assert uid == "uid-1"

def test_download_and_upload_images_upload_failure(monkeypatch):
    # simulate upload_image raising for one size by monkeypatching upload_image
    def fake_upload(data, ctype, dest):
        if dest.endswith("/240.jpg"):
            raise RuntimeError("upload fail")
        return f"https://storage.googleapis.com/dummy-bucket/{dest}"
    monkeypatch.setattr(app_img, "upload_image", fake_upload)

    monkeypatch.setattr(app_img, "generate_uuid", lambda i: "uid-xyz")
    called = []
    monkeypatch.setattr(app_img, "update_image_path", lambda pid, name, url: called.append((pid, name, url)))

    # make requests.get succeed for downloads
    monkeypatch.setattr(app_img.requests, "get", lambda url, timeout=10: MockResp(b"ok", 200, {"Content-Type": "image/jpeg"}))

    results, uid = app_img.download_and_upload_images("99", 3003, "img-kkk")
    assert any(src.endswith("/240.jpg") and uploaded is None for src, uploaded in results)
    # update_image_path called only for successful uploads (2)
    assert len(called) == 2
    assert uid == "uid-xyz"
