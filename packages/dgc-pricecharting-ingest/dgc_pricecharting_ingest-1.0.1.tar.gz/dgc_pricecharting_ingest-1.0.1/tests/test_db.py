# tests/test_cards_client.py
import os
from datetime import datetime, timezone
import types
import pytest

import dgc_pricecharting_ingest.db as cards_client


class FakeCollection:
    def __init__(self):
        self.calls = []

    def update_one(self, filter_doc, update_doc):
        # record a shallow copy so assertions can't accidentally mutate them later
        self.calls.append((filter_doc.copy(), _deepcopy(update_doc)))
        # Simulate pymongo UpdateResult-like object if needed (not used here)
        class R:
            matched_count = 1
            modified_count = 1
        return R()


class FakeDB:
    def __init__(self, collection):
        self._collection = collection

    def __getitem__(self, item):
        if item == cards_client.COLLECTION:
            return self._collection
        raise KeyError(item)


def _deepcopy(obj):
    """Minimal deep copy used for dicts/lists (avoid importing copy to keep tests simple)."""
    if isinstance(obj, dict):
        return {k: _deepcopy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deepcopy(v) for v in obj]
    return obj


@pytest.fixture(autouse=True)
def env_and_reset(monkeypatch):
    """
    Ensure module-level cache is reset between tests and MONGO_URI_PRICES is set.
    The module reads MONGO_URI_PRICES at import time into cards_client.MONGO_URI_PRICES,
    so we manipulate that attribute directly for tests.
    """
    # ensure MONGO_URI_PRICES is set for normal tests
    monkeypatch.setenv("MONGO_URI_PRICES", "mongodb://test:27017")
    # Also make sure the module-level variable matches (module captured it at import)
    monkeypatch.setattr(cards_client, "MONGO_URI_PRICES", os.getenv("MONGO_URI_PRICES"), raising=False)

    # Reset cached db/client/collection between tests
    monkeypatch.setattr(cards_client, "_db_client", None, raising=False)
    monkeypatch.setattr(cards_client, "_collection", None, raising=False)

    yield

    # cleanup after test
    monkeypatch.setattr(cards_client, "_db_client", None, raising=False)
    monkeypatch.setattr(cards_client, "_collection", None, raising=False)


def test_get_collection_happy_path(monkeypatch):
    fake_coll = FakeCollection()
    fake_db = FakeDB(fake_coll)

    # Replace the module's _mongo_cache.get_db to return our fake_db
    def fake_get_db(uri, dbname):
        assert uri == cards_client.MONGO_URI_PRICES
        assert dbname == cards_client.DB
        return fake_db

    # patch the _mongo_cache object method
    monkeypatch.setattr(cards_client._mongo_cache, "get_db", fake_get_db, raising=True)

    # Ensure no cached collection yet
    cards_client._collection = None
    coll = cards_client._get_collection()
    assert coll is fake_coll

    # subsequent call should return the cached collection and not call get_db again
    cards_client._collection = coll
    coll2 = cards_client._get_collection()
    assert coll2 is coll


def test_get_collection_raises_when_env_missing(monkeypatch):
    # Simulate environment missing by setting module-level constant to None
    monkeypatch.setenv("MONGO_URI_PRICES", "")
    monkeypatch.setattr(cards_client, "MONGO_URI_PRICES", None, raising=False)

    # Clear any cached references
    monkeypatch.setattr(cards_client, "_db_client", None, raising=False)
    monkeypatch.setattr(cards_client, "_collection", None, raising=False)

    with pytest.raises(RuntimeError):
        cards_client._get_collection()


def test_mark_card_uploaded_updates_correct_fields(monkeypatch):
    fake_coll = FakeCollection()
    fake_db = FakeDB(fake_coll)

    monkeypatch.setattr(cards_client._mongo_cache, "get_db", lambda uri, db: fake_db, raising=True)
    # ensure fresh cache
    cards_client._db_client = None
    cards_client._collection = None

    cards_client.mark_card_uploaded(42, "image_id")

    assert len(fake_coll.calls) == 1
    filt, upd = fake_coll.calls[0]
    assert filt == {"id": 42}
    # check $set and $unset
    assert "$set" in upd
    s = upd["$set"]
    assert s["uploadStatus.imagesUploaded"] is True
    assert isinstance(s["updatedAt"], datetime)
    assert "$unset" in upd and upd["$unset"] == {"uploadStatus.invalidUrl": "", "uploadStatus.noImage": ""}
    # ensure timezone-aware (UTC)
    assert s["updatedAt"].tzinfo is not None and s["updatedAt"].tzinfo.utcoffset(s["updatedAt"]) == timezone.utc.utcoffset(s["updatedAt"])


def test_mark_card_noimage_updates_correct_fields(monkeypatch):
    fake_coll = FakeCollection()
    fake_db = FakeDB(fake_coll)
    monkeypatch.setattr(cards_client._mongo_cache, "get_db", lambda uri, db: fake_db, raising=True)
    cards_client._db_client = None
    cards_client._collection = None

    cards_client.mark_card_noimage(99)

    assert len(fake_coll.calls) == 1
    filt, upd = fake_coll.calls[0]
    assert filt == {"id": 99}
    s = upd["$set"]
    assert s["uploadStatus.noImage"] is True
    assert isinstance(s["updatedAt"], datetime)
    assert upd["$unset"] == {"uploadStatus.invalidUrl": ""}
    # ensure timezone-aware (UTC)
    assert s["updatedAt"].tzinfo is not None and s["updatedAt"].tzinfo.utcoffset(s["updatedAt"]) == timezone.utc.utcoffset(s["updatedAt"])


def test_mark_card_invalid_url_sets_flag(monkeypatch):
    fake_coll = FakeCollection()
    fake_db = FakeDB(fake_coll)
    monkeypatch.setattr(cards_client._mongo_cache, "get_db", lambda uri, db: fake_db, raising=True)
    cards_client._db_client = None
    cards_client._collection = None

    cards_client.mark_card_invalid_url(7)

    assert len(fake_coll.calls) == 1
    filt, upd = fake_coll.calls[0]
    assert filt == {"id": 7}
    s = upd["$set"]
    assert s["uploadStatus.invalidUrl"] is True
    assert isinstance(s["updatedAt"], datetime)
    # ensure timezone-aware (UTC)
    assert s["updatedAt"].tzinfo is not None and s["updatedAt"].tzinfo.utcoffset(s["updatedAt"]) == timezone.utc.utcoffset(s["updatedAt"])


def test_update_image_path_sets_field(monkeypatch):
    fake_coll = FakeCollection()
    fake_db = FakeDB(fake_coll)
    monkeypatch.setattr(cards_client._mongo_cache, "get_db", lambda uri, db: fake_db, raising=True)
    cards_client._db_client = None
    cards_client._collection = None

    cards_client.update_image_path(123, "small", "https://cdn.example/img.jpg")

    assert len(fake_coll.calls) == 1
    filt, upd = fake_coll.calls[0]
    assert filt == {"id": 123}
    s = upd["$set"]
    assert s["images.small"] == "https://cdn.example/img.jpg"
    assert isinstance(s["updatedAt"], datetime)
    # ensure timezone-aware (UTC)
    assert s["updatedAt"].tzinfo is not None and s["updatedAt"].tzinfo.utcoffset(s["updatedAt"]) == timezone.utc.utcoffset(s["updatedAt"])


def test_update_card_number_sets_card_number(monkeypatch):
    fake_coll = FakeCollection()
    fake_db = FakeDB(fake_coll)
    monkeypatch.setattr(cards_client._mongo_cache, "get_db", lambda uri, db: fake_db, raising=True)
    cards_client._db_client = None
    cards_client._collection = None

    cards_client.update_card_number(555, "A-1")

    assert len(fake_coll.calls) == 1
    filt, upd = fake_coll.calls[0]
    assert filt == {"id": 555}
    s = upd["$set"]
    assert s["cardNumber"] == "A-1"
    assert isinstance(s["updatedAt"], datetime)
    # ensure timezone-aware (UTC)
    assert s["updatedAt"].tzinfo is not None and s["updatedAt"].tzinfo.utcoffset(s["updatedAt"]) == timezone.utc.utcoffset(s["updatedAt"])


def test_mark_card_deleted_sets_deleted_and_updatedAt(monkeypatch):
    fake_coll = FakeCollection()
    fake_db = FakeDB(fake_coll)
    monkeypatch.setattr(cards_client._mongo_cache, "get_db", lambda uri, db: fake_db, raising=True)
    cards_client._db_client = None
    cards_client._collection = None

    # call function
    cards_client.mark_card_deleted(314)

    assert len(fake_coll.calls) == 1
    filt, upd = fake_coll.calls[0]
    assert filt == {"id": 314}
    # $set should set deleted True and updatedAt a datetime with tzinfo
    assert "$set" in upd
    s = upd["$set"]
    assert s["deleted"] is True
    assert isinstance(s["updatedAt"], datetime)
    # ensure timezone-aware (UTC)
    assert s["updatedAt"].tzinfo is not None and s["updatedAt"].tzinfo.utcoffset(s["updatedAt"]) == timezone.utc.utcoffset(s["updatedAt"])
