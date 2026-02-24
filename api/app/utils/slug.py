"""Slug generation utility."""
import re
import uuid


def generate_slug(text: str, max_length: int = 100) -> str:
    """Generate a URL-safe slug from text.
    
    Args:
        text: The text to convert to a slug
        max_length: Maximum length of the slug
        
    Returns:
        A URL-safe slug
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces and underscores with hyphens
    slug = slug.replace(" ", "-").replace("_", "-")
    
    # Remove any character that is not alphanumeric, hyphen, or period
    slug = re.sub(r"[^a-z0-9\-.]", "", slug)
    
    # Replace multiple consecutive hyphens with a single hyphen
    slug = re.sub(r"-+", "-", slug)
    
    # Remove leading and trailing hyphens
    slug = slug.strip("-")
    
    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    
    return slug


def make_unique_slug(base_slug: str, existing_slugs: set[str]) -> str:
    """Make a slug unique by appending a suffix if needed.
    
    Args:
        base_slug: The base slug to make unique
        existing_slugs: Set of existing slugs to check against
        
    Returns:
        A unique slug
    """
    if base_slug not in existing_slugs:
        return base_slug
    
    # Try appending numbers first
    for i in range(1, 100):
        candidate = f"{base_slug}-{i}"
        if candidate not in existing_slugs:
            return candidate
    
    # If still not unique, append a short UUID
    short_uuid = str(uuid.uuid4())[:8]
    return f"{base_slug}-{short_uuid}"
