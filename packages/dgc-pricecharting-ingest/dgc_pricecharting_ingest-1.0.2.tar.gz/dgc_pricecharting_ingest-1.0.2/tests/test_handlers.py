import sys
from types import ModuleType
import pytest

# -------------------------------------------------
# firebase_admin FULL MOCK (must load before app)
# -------------------------------------------------
mock_firebase_admin = ModuleType("firebase_admin")
mock_firebase_admin._apps = {}

mock_credentials = ModuleType("firebase_admin.credentials")
mock_credentials.Certificate = staticmethod(lambda _: "mock-cert")
mock_credentials.ApplicationDefault = staticmethod(lambda: "mock-app-default")

mock_storage = ModuleType("firebase_admin.storage")

class MockBlob:
    def __init__(self, path, bucket="test-bucket"):
        self.path = path
        self.public_url = f"https://storage.googleapis.com/{bucket}/{path}"

    def upload_from_filename(self, *a, **k): ...
    def upload_from_string(self, *a, **k): ...
    def make_public(self): ...

class MockBucket:
    def __init__(self, name="test-bucket"):
        self.name = name
    def blob(self, path):
        return MockBlob(path, self.name)

mock_storage.bucket = lambda name=None: MockBucket(name or "test-bucket")

mock_firebase_admin.credentials = mock_credentials
mock_firebase_admin.storage = mock_storage
mock_firebase_admin.initialize_app = lambda *a, **k: None

sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.credentials"] = mock_credentials
sys.modules["firebase_admin.storage"] = mock_storage

# -------------------------------------------------
# Import module under test
# -------------------------------------------------
import dgc_pricecharting_ingest.handlers as app_module

# -------------------------------------------------
# Fixtures
# -------------------------------------------------
@pytest.fixture(autouse=True)
def reset_cache():
    app_module._manual_url_cache = None
    yield

@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c

class MockResponse:
    def __init__(self, text="", status=200):
        self.text = text
        self.status_code = status
        self.headers = {"Content-Type": "text/html"}

# -------------------------------------------------
# Common success patch
# -------------------------------------------------
def patch_success(monkeypatch):
    monkeypatch.setattr(app_module, "verify_request", lambda *a, **k: True)
    monkeypatch.setattr(app_module, "pricecharting_url", lambda c, p: p)
    monkeypatch.setattr(app_module, "extract_pricecharting_id", lambda h: h.split("-",1)[1])
    monkeypatch.setattr(app_module, "extract_card_number", lambda _: None)
    monkeypatch.setattr(app_module, "product_exists", lambda _: True)
    monkeypatch.setattr(
        app_module.requests,
        "get",
        lambda *a, **k: MockResponse(a[0], 200)
    )
    monkeypatch.setattr(
        app_module,
        "extract_image_info",
        lambda _: {"image_id": "img", "no_image": False}
    )
    monkeypatch.setattr(
        app_module,
        "download_and_upload_images",
        lambda *_: ([("src", "dest")], "stored")
    )
    monkeypatch.setattr(app_module, "mark_card_uploaded", lambda *_: None)
    monkeypatch.setattr(app_module, "mark_card_noimage", lambda *_: None)
    monkeypatch.setattr(app_module, "mark_card_invalid_url", lambda *_: None)
    monkeypatch.setattr(app_module, "mark_card_deleted", lambda *_: None)
    monkeypatch.setattr(app_module, "update_card_number", lambda *_: None)

# -------------------------------------------------
# AUTH / REQUEST VALIDATION
# -------------------------------------------------
def test_unauthorized(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_request", lambda *a, **k: False)
    r = client.post("/", json={})
    assert r.status_code == 403

def test_not_json(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_request", lambda *a, **k: True)
    r = client.post("/", data="x", content_type="text/plain")
    assert r.status_code == 400

def test_invalid_json_body(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_request", lambda *a, **k: True)
    r = client.post("/", data="{bad}", content_type="application/json")
    assert r.status_code == 400

# -------------------------------------------------
# INPUT SHAPE / ID HANDLING
# -------------------------------------------------
def test_missing_required_fields(client, monkeypatch):
    patch_success(monkeypatch)
    r = client.post("/", json={"id": 1})
    assert r.get_json()["failed"] == 1

def test_invalid_id_string(client, monkeypatch):
    patch_success(monkeypatch)
    r = client.post("/", json={
        "_id": "x", "id": "abc", "console_name": "X", "product_name": "pid-1"
    })
    assert r.get_json()["failed"] == 1

def test_non_dict_item_in_batch(client, monkeypatch):
    patch_success(monkeypatch)
    r = client.post("/", json=[{"id":1,"console_name":"X","product_name":"pid-1"}, "bad"])
    assert r.get_json()["failed"] == 1

# -------------------------------------------------
# MANUAL URL CACHE (32–60)
# -------------------------------------------------
def test_manual_url_cache_api_failure(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_request", lambda *a, **k: True)
    monkeypatch.setattr(
        app_module.requests,
        "get",
        lambda *a, **k: MockResponse("", 500)
    )
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    assert r.status_code == 200

# -------------------------------------------------
# PRICECHARTING FETCH FAILURES (84–95)
# -------------------------------------------------
def test_pricecharting_404(client, monkeypatch):
    patch_success(monkeypatch)
    monkeypatch.setattr(
        app_module.requests,
        "get",
        lambda *a, **k: MockResponse("", 404)
    )
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    assert r.get_json()["failed"] == 1

def test_missing_pid_marks_deleted(client, monkeypatch):
    patch_success(monkeypatch)
    monkeypatch.setattr(app_module, "extract_pricecharting_id", lambda _: None)
    monkeypatch.setattr(app_module, "product_exists", lambda _: False)
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    assert r.get_json()["skipped"] == 1

# -------------------------------------------------
# PID MISMATCH / DELETE PATHS (102–109)
# -------------------------------------------------
def test_pid_mismatch_deleted(client, monkeypatch):
    patch_success(monkeypatch)
    monkeypatch.setattr(app_module, "extract_pricecharting_id", lambda _: "999")
    monkeypatch.setattr(app_module, "product_exists", lambda _: False)
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    assert r.get_json()["skipped"] == 1

# -------------------------------------------------
# IMAGE EXTRACTION BRANCHES (116–138)
# -------------------------------------------------
def test_missing_product_details(client, monkeypatch):
    patch_success(monkeypatch)
    monkeypatch.setattr(app_module, "extract_image_info", lambda _: None)
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    assert r.get_json()["skipped"] == 1

def test_no_image_flag(client, monkeypatch):
    patch_success(monkeypatch)
    monkeypatch.setattr(
        app_module, "extract_image_info",
        lambda _: {"image_id": None, "no_image": True}
    )
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    assert r.get_json()["skipped"] == 1

def test_invalid_image_src(client, monkeypatch):
    patch_success(monkeypatch)
    monkeypatch.setattr(
        app_module, "extract_image_info",
        lambda _: {"image_id": None, "no_image": False}
    )
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    assert r.get_json()["skipped"] == 1

# -------------------------------------------------
# UPLOAD FAILURE / DB FAILURE (152–171)
# -------------------------------------------------
def test_all_uploads_fail_marks_noimage(client, monkeypatch):
    patch_success(monkeypatch)
    monkeypatch.setattr(
        app_module,
        "download_and_upload_images",
        lambda *_: ([("src", None)], None)
    )
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    assert r.get_json()["failed"] == 1

def test_mark_uploaded_exception(client, monkeypatch):
    patch_success(monkeypatch)
    monkeypatch.setattr(
        app_module,
        "mark_card_uploaded",
        lambda *_: (_ for _ in ()).throw(RuntimeError("db error"))
    )
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    body = r.get_json()
    assert body["failed"] == 1
    assert "mark_card_uploaded error" in body["details"][0]["reason"]

# -------------------------------------------------
# INTERNAL EXCEPTION SAFETY NET (196–201)
# -------------------------------------------------
def test_internal_exception_handled(client, monkeypatch):
    patch_success(monkeypatch)
    monkeypatch.setattr(
        app_module, "extract_image_info",
        lambda *_: (_ for _ in ()).throw(Exception("boom"))
    )
    r = client.post("/", json={
        "_id":"x","id":1,"console_name":"X","product_name":"pid-1"
    })
    assert r.get_json()["failed"] == 1

# -------------------------------------------------
# HAPPY PATH (baseline sanity)
# -------------------------------------------------
def test_single_success(client, monkeypatch):
    patch_success(monkeypatch)
    r = client.post("/", json={
        "_id":"x","id":123,"console_name":"NES","product_name":"pid-123"
    })
    body = r.get_json()
    assert body["uploaded"] == 1
    assert body["failed"] == 0
