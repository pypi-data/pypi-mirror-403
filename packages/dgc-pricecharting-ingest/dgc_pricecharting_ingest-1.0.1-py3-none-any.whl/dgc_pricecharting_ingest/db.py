import os
from datetime import datetime, timezone
from opticedge_cloud_utils.mongo_cache import MongoCache

MONGO_URI_PRICES = os.getenv("MONGO_URI_PRICES")
DB = "pricecharting"
COLLECTION = "cards"

_mongo_cache = MongoCache()
_db_client = None
_collection = None


def _get_collection():
    """Lazily obtain and cache the collection object (connection reuse)."""
    global _db_client, _collection
    if _collection is None:
        if not MONGO_URI_PRICES:
            raise RuntimeError("MONGO_URI_PRICES environment variable is not set")
        if _db_client is None:
            _db_client = _mongo_cache.get_db(MONGO_URI_PRICES, DB)
        _collection = _db_client[COLLECTION]
    return _collection


def mark_card_uploaded(card_id: int, image_id: str):
    """Mark card as imagesUploaded=True and unset invalidUrl."""
    _get_collection().update_one(
        {"id": card_id},
        {
            "$set": {
                "uploadStatus.imagesUploaded": True,
                "imageId": image_id,
                "updatedAt": datetime.now(timezone.utc)
            },
            "$unset": {
                "uploadStatus.invalidUrl": "",
                "uploadStatus.noImage": ""
            }
        },
    )


def mark_card_noimage(card_id: int):
    """Mark card as noImage=True and unset invalidUrl."""
    _get_collection().update_one(
        {"id": card_id},
        {
            "$set": {
                "uploadStatus.noImage": True,
                "updatedAt": datetime.now(timezone.utc)
            },
            "$unset": {"uploadStatus.invalidUrl": ""}
        },
    )


def mark_card_deleted(card_id: int):
    """Mark card as deleted: unset invalidUrl and update updatedAt timestamp."""
    _get_collection().update_one(
        {"id": card_id},
        {
            "$set": {
                "deleted": True,
                "updatedAt": datetime.now(timezone.utc)
            }
        },
    )


def mark_card_invalid_url(card_id: int):
    """Mark card as invalidUrl=True."""
    _get_collection().update_one(
        {"id": card_id},
        {"$set": {
            "uploadStatus.invalidUrl": True,
            "updatedAt": datetime.now(timezone.utc)
        }},
    )


def update_image_path(card_id: int, size: str, url: str):
    _get_collection().update_one(
        {"id": card_id},
        {"$set": {
            f"images.{size}": url,
            "updatedAt": datetime.now(timezone.utc)
        }},
    )


def update_card_number(card_id: int, card_number: str | None):
    _get_collection().update_one(
        {"id": card_id},
        {"$set": {
            "cardNumber": card_number,
            "updatedAt": datetime.now(timezone.utc)
        }},
    )
