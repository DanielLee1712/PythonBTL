from django.utils.text import slugify as django_slugify
import uuid


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name."""
    return django_slugify(name, allow_unicode=True)


def generate_sku(prefix: str = 'PRD') -> str:
    """Generate a unique SKU."""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
