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
