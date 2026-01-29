from __future__ import annotations
from .string_helpers import camel_to_kebab, has_mustache
from typing import Any, Dict, Optional
import html
from tailwind_merge import TailwindMerge
from markupsafe import Markup

_twm = TailwindMerge()

# Map Python-safe names to HTML attributes
ALIAS_MAP = {
    "class_name": "class",
    "className": "class",
    "html_for": "for",
    "htmlFor": "for"
}


def merge_classes(*classes: Any) -> str:
    parts: list[str] = []
    has_dynamic = False

    for c in classes:
        if not c:
            continue
        if isinstance(c, (list, tuple, set)):
            s = " ".join(str(x) for x in c if x)
        else:
            s = str(c).strip()
        if s:
            parts.append(s)
            if has_mustache(s):
                has_dynamic = True

    if not parts:
        return ""
    if has_dynamic:
        return " ".join(parts)

    return _twm.merge(*parts)


def _to_attr_value(v: Any) -> Optional[str]:
    # XML-strict: booleans should have explicit values
    if v is None:
        return None
    if isinstance(v, bool):
        return "true" if v else None  # omit false
    if isinstance(v, (list, tuple, set)):
        s = " ".join(str(x) for x in v if x)
        return s if s else None
    s = str(v)
    return s if s != "" else None


def get_attributes(props: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> Markup:
    """
    Build ONE attribute string.
    - Resolves Aliases first (className -> class).
    - Normalizes ALL keys to kebab-case (dataSlot -> data-slot).
    - Merges defaults (props) and overrides to ensure correct precedence.
    - Returns Markup() so Jinja does not double-escape the quotes.
    """

    final_attrs: Dict[str, str] = {}

    # Helper to process a dictionary into the final map
    def process_source(source: Dict[str, Any]):
        if not source:
            return

        for k, v in source.items():
            if not k:
                continue

            # 1. Check Alias Map first (e.g., class_name -> class)
            key_name = ALIAS_MAP.get(k, k)

            # 2. Normalize to Kebab Case ALWAYS
            # This ensures that 'dataSlot' (from compiler) overwrites 'data-slot' (from defaults)
            # regardless of whether the value has mustache syntax or not.
            final_key = camel_to_kebab(key_name)

            # 3. Process value to string
            val = _to_attr_value(v)

            if val is not None:
                final_attrs[final_key] = val

    # 1. Process defaults (props) first
    process_source(props)

    # 2. Process overrides second (this overwrites keys from step 1)
    if overrides:
        process_source(overrides)

    # 3. Build string
    parts: list[str] = []
    # Sorting keys for consistent output
    for k in sorted(final_attrs.keys()):
        v = final_attrs[k]
        parts.append(f'{k}="{html.escape(v, quote=True)}"')

    # 4. Return as Safe Markup
    return Markup(" ".join(parts))
