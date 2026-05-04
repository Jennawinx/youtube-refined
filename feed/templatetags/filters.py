from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key in templates.
    Usage: {{ dict|get_item:"key_name" }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def get_block_at_hour(blocks, hour):
    """Return the first block that starts at the provided hour."""
    if not blocks:
        return None
    for block in blocks:
        if block.start_hour == hour:
            return block
    return None
