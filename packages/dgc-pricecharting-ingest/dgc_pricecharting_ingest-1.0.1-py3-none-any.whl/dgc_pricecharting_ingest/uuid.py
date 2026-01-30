import uuid
from datetime import datetime, timezone

def generate_uuid(doc_id: str) -> uuid.UUID:
    """
    Generate a UUID based on the document ID,
    and the current UTC timestamp.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    data = f"{doc_id}:{timestamp}"
    return uuid.uuid5(uuid.NAMESPACE_DNS, data)
