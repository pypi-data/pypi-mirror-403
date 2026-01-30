import os
from typing import List, Optional, Tuple, Dict
import firebase_admin
import requests
from firebase_admin import credentials, storage, initialize_app
from dgc_pricecharting_ingest.db import update_image_path
from dgc_pricecharting_ingest.uuid import generate_uuid


# Load database URL from environment
FIREBASE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# Initialize Firebase app only once
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    initialize_app(cred, {
        'storageBucket': FIREBASE_BUCKET
    })

bucket = storage.bucket()


def download_image(url: str, timeout: int = 10) -> Tuple[Optional[bytes], Optional[str]]:
    """Download image bytes from a given URL."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return resp.content, content_type
    except Exception as e:
        print(f"[download_image] failed for {url}: {e}")
        return None, None
    

def upload_image(data: bytes, content_type: str, dest_path: str) -> str:
    """Upload image bytes to Firebase Storage (private by default)."""
    blob = bucket.blob(dest_path)
    blob.upload_from_string(data, content_type=content_type)
    blob.make_public()
    return blob.public_url


def download_and_upload_images(
    _id: str,
    pid: int,
    image_id: str,
    sizes: Dict[str, int] = {"tiny": 120, "small": 240, "normal": 1600},
    dest_prefix: str = "card_images"
) -> Tuple[List[Tuple[str, Optional[str]]], str]:
    """
    Download 3 images (120, 240, 1600) from PriceCharting
    and upload them to Firebase Storage under folder = PID.
    """
    results = []
    uid = generate_uuid(_id)

    for name, size in sizes.items():
        url = f"https://storage.googleapis.com/images.pricecharting.com/{image_id}/{size}.jpg"
        data, content_type = download_image(url)
        if not data:
            results.append((url, None))
            continue

        dest_path = f"{dest_prefix}/{uid}/{size}.jpg"
        try:
            uploaded = upload_image(data, content_type, dest_path)
            update_image_path(pid, name, uploaded)
            results.append((url, uploaded))
        except Exception as e:
            print(f"[upload_image] failed for {url}: {e}")
            results.append((url, None))

    return results, str(uid)
