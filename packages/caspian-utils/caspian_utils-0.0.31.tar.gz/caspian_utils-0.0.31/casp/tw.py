from __future__ import annotations
from typing import Any
from tailwind_merge import TailwindMerge

_twm = TailwindMerge()


def tw_merge(*values: Any) -> str:
    """
    Merge Tailwind class strings (and optionally lists/tuples/sets) into a single
    conflict-resolved class string using tailwind-merge.
    """
    parts: list[str] = []

    for v in values:
        if not v:
            continue

        if isinstance(v, (list, tuple, set)):
            chunk = " ".join(str(x) for x in v if x)
        else:
            chunk = str(v).strip()

        if chunk:
            parts.append(chunk)

    if not parts:
        return ""

    # TailwindMerge.merge accepts multiple class strings. :contentReference[oaicite:2]{index=2}
    return _twm.merge(*parts)
