import re
from typing import Optional, Dict
from bs4 import BeautifulSoup


def extract_pricecharting_id(html: str) -> Optional[str]:
    """
    Extract PriceCharting ID from <div id="full_details">.
    - Returns the first numeric token (e.g. "7307259") or None.
    - No fallback searches elsewhere on the page.
    """
    soup = BeautifulSoup(html, "html.parser")
    full = soup.find("div", id="full_details")
    if not full:
        return None

    # Look only at <td class="title"> nodes inside #full_details
    for title_td in full.select("td.title"):
        # normalize text like "PriceCharting ID:" (case/whitespace tolerant)
        title_text = title_td.get_text(strip=True).lower()
        if re.match(r"^pricecharting\s*id:?\s*$", title_text):
            details_td = title_td.find_next_sibling("td")
            if not details_td:
                return None
            details_text = details_td.get_text(separator=" ", strip=True)
            m = re.search(r"\d+", details_text)
            return m.group(0) if m else None

    # nothing found inside #full_details
    return None


def extract_card_number(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    full = soup.find("div", id="full_details")
    if not full:
        return None

    # Look only at <td class="title"> nodes inside #full_details
    for title_td in full.select("td.title"):
        # normalize text like "PriceCharting ID:" (case/whitespace tolerant)
        title_text = title_td.get_text(strip=True).lower()
        if re.match(r"^card\s*number:?\s*$", title_text):
            details_td = title_td.find_next_sibling("td")
            if not details_td:
                return None
            details_text = details_td.get_text(separator=" ", strip=True)
            cleaned = details_text.strip().lstrip("#").strip()
            return cleaned or None

    # nothing found inside #full_details
    return None


def extract_image_info(html: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Extract PriceCharting image information from the product detail page.

    Returns:
        {
            "image_id": <str or None>,
            "no_image": <bool>
        }
    or None if the product_details section is missing entirely.
    """
    soup = BeautifulSoup(html, "html.parser")
    product_div = soup.find("div", id="product_details")
    if not product_div:
        return None  # no product info at all

    img_tag = product_div.select_one("div.cover>a:nth-child(1)>img")
    if not img_tag or not img_tag.get("src"):
        # no img tag at all — not marked as "no image", just no valid src
        return {"image_id": None, "no_image": False}

    src = img_tag["src"].strip()

    # Case 1: explicit placeholder image
    if "no-image-available" in src.lower():
        return {"image_id": None, "no_image": True}

    # Case 2: valid hosted image on PriceCharting
    m = re.search(
        r"https://storage\.googleapis\.com/images\.pricecharting\.com/([^/]+)/\d+\.jpg",
        src
    )
    if m:
        return {"image_id": m.group(1), "no_image": False}

    # Case 3: other/unexpected src — treat as not "no-image" but no valid ID
    return {"image_id": None, "no_image": False}
