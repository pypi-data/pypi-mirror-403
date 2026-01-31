import threading
from .client import central_cache_flush


def flush_cache(entity_id, entity_type, api_url, api_key):
    """
    Asynchronously trigger centralized cache invalidation.
    
    This is a fire-and-forget operation that won't block your application.
    
    Args:
        entity_id (int): The ID of the entity to invalidate
        entity_type (str): Type of entity (e.g., "college", "exam", "article")
        api_url (str): Full URL of the cache invalidation API endpoint
        api_key (str): API key for authentication
    
    Example:
        >>> flush_cache(
        ...     entity_id=123,
        ...     entity_type="college",
        ...     api_url="Invalidate URL",
        ...     api_key="your-api-key"
        ... )
    """
    threading.Thread(
        target=central_cache_flush,
        args=(entity_id, entity_type, api_url, api_key),
        daemon=True,
    ).start()
