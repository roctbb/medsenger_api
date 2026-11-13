"""Optional SQLAlchemy integration for committed, semantic cache invalidations.

No API endpoints or wire formats are introduced. Install the ``cache`` extra
and register a pure projection for each model that contributes to the cache.
"""

from .outbox import CacheUpdateOutbox, create_table

__all__ = ['CacheUpdateOutbox', 'create_table']
