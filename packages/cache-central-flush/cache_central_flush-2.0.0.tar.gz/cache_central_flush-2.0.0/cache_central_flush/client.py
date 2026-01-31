import requests


def central_cache_flush(entity_id, entity_type, api_url, api_key):
    """
    Trigger centralized cache invalidation.
    
    Args:
        entity_id (int): The ID of the entity to invalidate
        entity_type (str): Type of entity (e.g., "college", "exam", "article")
        api_url (str): Full URL of the cache invalidation API endpoint
        api_key (str): API key for authentication
    """
    payload = {
        "entity_id": entity_id,
        "entity_type": entity_type,
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    try:
        requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=2,
        )
    except Exception:
        # fire-and-forget: don't break caller
        pass
