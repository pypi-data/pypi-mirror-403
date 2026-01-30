import os
import requests
import traceback
from typing import Any, Dict, List, Optional

from flask import Flask, request, jsonify
from opticedge_cloud_utils.auth import verify_request
from dgc_pricecharting_ingest.url import pricecharting_url
from dgc_pricecharting_ingest.bs import extract_pricecharting_id, extract_image_info, extract_card_number
from dgc_pricecharting_ingest.img import download_and_upload_images
from dgc_pricecharting_ingest.db import mark_card_uploaded, mark_card_noimage, mark_card_invalid_url, mark_card_deleted, update_card_number
from dgc_pricecharting_ingest.pricecharting import product_exists

app = Flask(__name__)

ALLOWED_SERVICE_ACCOUNT = os.getenv("ALLOWED_SERVICE_ACCOUNT")
ALLOWED_AUDIENCE = os.getenv("ALLOWED_AUDIENCE")

card_manual_urls = {
    10080208: 'https://www.pricecharting.com/game/pokemon-japanese-promo/team%e2%80%afrocket%27s%e2%80%afmeowth-259sv-p',
    69402: "https://www.pricecharting.com/game/lego-dimensions/fantastic-beasts-and-where-to-find-them-story-pack",
    69398: "https://www.pricecharting.com/game/lego-dimensions/green-arrow",
    69434: "https://www.pricecharting.com/game/lego-dimensions/the-goonies-level-pack",
    69447: "https://www.pricecharting.com/game/lego-dimensions/the-simpsons-bart-simpson-fun-pack",
    5065766: "https://www.pricecharting.com/game/zx-spectrum/a,b,c-lift-off",
    807172: "https://www.pricecharting.com/game/pokemon-sword-&-shield/marnie-holo-169"
}

def _get_card_manual_url(card_id: int) -> str | None:
    return card_manual_urls.get(card_id)

def _to_int_id(val: Any) -> Optional[int]:
    """Safely convert id to int if possible, otherwise return None."""
    if isinstance(val, int):
        return val
    if isinstance(val, str) and val.isdigit():
        return int(val)
    try:
        # try loose conversion for numeric strings like "123"
        return int(val)
    except Exception:
        return None


def _process_single_card(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single TaskData-shaped payload:
      { id, console_name, product_name }
    Returns a dict with result details.
    """
    result: Dict[str, Any] = {
        "id": item.get("id"),
        "status": None,
        "reason": None,
        "uploads": None,
    }

    # Required fields matching TaskData
    _id = item.get('_id')
    raw_id = item.get("id")
    console_name = item.get("console_name")
    product_name = item.get("product_name")

    # Validate required fields
    if not (raw_id is not None and console_name and product_name):
        result["status"] = "failed"
        result["reason"] = "missing required fields (id, console_name, product_name)"
        print(f"Skipping card due to missing fields: {item}")
        return result

    # Coerce id to int (TaskData.id is a number)
    card_id_int = _to_int_id(raw_id)
    if card_id_int is None:
        result["status"] = "failed"
        result["reason"] = f"invalid id (must be numeric): {raw_id}"
        print(f"Invalid id for item: {raw_id}")
        return result

    # keep numeric id in result for clarity
    result["id"] = card_id_int

    try:
        card_url = _get_card_manual_url(card_id_int)
        if card_url is None:
            card_url = pricecharting_url(console_name, product_name)
        resp = requests.get(card_url, timeout=10)
        if resp.status_code != 200:
            result["status"] = "failed"
            result["reason"] = f"pricecharting returned status {resp.status_code}"
            print(f"Failed to fetch {card_url}: status {resp.status_code}")
            return result

        html = resp.text
        extracted_pid = extract_pricecharting_id(html)

        # extracted_pid might be int-like or str; normalize and validate
        if extracted_pid is None:
            result["status"] = "skipped"
            result["reason"] = "missing pricecharting pid"
            print(f"Missing pid for card id {card_id_int}")
            mark_card_invalid_url(card_id_int)
            if product_exists(card_id_int) is False:
                mark_card_deleted(card_id_int)
            return result

        extracted_pid_str = str(extracted_pid).strip()
        if not extracted_pid_str.isdigit():
            result["status"] = "skipped"
            result["reason"] = "invalid pricecharting pid"
            print(f"Invalid pid for card id {card_id_int}: {extracted_pid_str}")
            return result

        # Compare numeric pid to numeric id
        if int(extracted_pid_str) != card_id_int:
            result["status"] = "skipped"
            result["reason"] = "pid mismatch"
            print(f"PID mismatch for card {card_id_int}: extracted {extracted_pid_str}")
            if product_exists(card_id_int) is False:
                mark_card_deleted(card_id_int)
            return result
        
        card_number = extract_card_number(html)
        if card_number:
            update_card_number(
                card_id_int,
                None if card_number.lower() == "none" else card_number
            )

        info = extract_image_info(html)
        print(f"Image info for card {card_id_int}: {info}")

        if not info:
            # product_details div missing
            result["status"] = "skipped"
            result["reason"] = "Product details not found"
            print(f"Product details not found for card {card_id_int}")
            return result

        if info["no_image"]:
            # explicit placeholder detected
            result["status"] = "skipped"
            result["reason"] = "No image available"
            print(f"No image available for card {card_id_int}")
            mark_card_noimage(card_id_int)
            return result

        image_id = info["image_id"]
        if not image_id:
            # unexpected/malformed image src
            result["status"] = "skipped"
            result["reason"] = "Invalid image src"
            print(f"Invalid image src for card {card_id_int}")
            return result

        # download_and_upload_images should accept int id
        results, stored_image_id = download_and_upload_images(_id, card_id_int, image_id)

        # check any uploads succeeded (assumes results is iterable of (src, dest))
        any_success = any(dest is not None for _, dest in results)

        result["uploads"] = results
        if any_success:
            try:
                mark_card_uploaded(card_id_int, stored_image_id)
                result["status"] = "uploaded"
                print(f"Card {card_id_int} marked as imagesUploaded in MongoDB.")
            except Exception as db_err:
                result["status"] = "failed"
                result["reason"] = f"mark_card_uploaded error: {db_err}"
                print(f"Failed to mark card {card_id_int} in DB:", db_err)
        else:
            result["status"] = "failed"
            result["reason"] = "one or more image uploads failed"
            mark_card_noimage(card_id_int)
            print(f"Card {card_id_int} marked noImage, all uploads failed: {results}")

        return result
    except Exception:
        tb_str = traceback.format_exc()
        print(f"An error occurred while processing card {card_id_int}:\n{tb_str}")
        result["status"] = "failed"
        result["reason"] = "internal processing error"
        return result


@app.route("/", methods=["POST"])
def handler():
    # auth
    if not verify_request(request, ALLOWED_SERVICE_ACCOUNT, ALLOWED_AUDIENCE):
        return jsonify({"error": "Unauthorized"}), 403

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    request_json = request.get_json(silent=True)
    if request_json is None:
        print("Invalid request: No JSON body")
        return jsonify({"error": "Request must contain a valid JSON body"}), 400

    # Accept either a single TaskData object or a list (batch)
    if isinstance(request_json, list):
        items = request_json
    elif isinstance(request_json, dict):
        items = [request_json]
    else:
        return jsonify({"error": "Request JSON must be an object or an array of objects"}), 400

    details: List[Dict[str, Any]] = []
    uploaded = 0
    skipped = 0
    failed = 0

    for item in items:
        if not isinstance(item, dict):
            details.append({
                "id": None,
                "status": "failed",
                "reason": "item must be an object"
            })
            failed += 1
            continue

        res = _process_single_card(item)
        details.append(res)
        if res["status"] == "uploaded":
            uploaded += 1
        elif res["status"] == "skipped":
            skipped += 1
        else:
            failed += 1

    summary = {
        "processed": len(items),
        "uploaded": uploaded,
        "skipped": skipped,
        "failed": failed,
        "details": details
    }
    print(summary)

    return jsonify(summary), 200
