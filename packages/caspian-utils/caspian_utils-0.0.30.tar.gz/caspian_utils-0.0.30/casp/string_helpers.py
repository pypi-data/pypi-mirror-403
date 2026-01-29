import re


def camel_to_kebab(name):
    return re.sub(r'([a-z])([A-Z])', r'\1-\2', name).lower()


def kebab_to_camel(name):
    parts = name.split('-')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def has_mustache(value):
    if isinstance(value, str):
        return bool(re.search(r'\{[^}]+\}', value))
    if isinstance(value, list):
        return any(has_mustache(v) for v in value)
    return False
