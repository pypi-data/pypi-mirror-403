import re


BASE = "https://www.pricecharting.com/game"


def _simple_slug(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    # remove square brackets but keep contents
    s = s.replace("[", "").replace("]", "")
    # remove common punctuation we don't want
    for ch in ("#", ":", "/", ".", "?", "!"):
        s = s.replace(ch, "")
    # remove commas unless they are between two digits (keep 100,000)
    def comma_repl(m):
        i = m.start()
        # safe neighbor lookup
        left = s[i-1] if i > 0 else ""
        right = s[i+1] if i+1 < len(s) else ""
        return "," if (left.isdigit() and right.isdigit()) else ""
    s = re.sub(",", comma_repl, s)

    # collapse whitespace -> single hyphen
    s = re.sub(r'\s+', '-', s)
    # collapse multiple hyphens and trim edges
    s = re.sub(r'-{2,}', '-', s)
    return s


def pricecharting_url(console_name: str, product_name: str) -> str:
    return f"{BASE}/{_simple_slug(console_name)}/{_simple_slug(product_name)}"
