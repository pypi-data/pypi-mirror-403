from .string_helpers import camel_to_kebab
from .string_helpers import kebab_to_camel
from .string_helpers import has_mustache
import re
import uuid
import inspect
from typing import Dict, List, Optional, Tuple, Iterator, NamedTuple
from .component_decorator import Component, load_component_from_path
import os


# ============================================================================
# TOKENIZER-FIRST PREPASS (Robust component + attribute handling)
# ============================================================================

class AttrToken(NamedTuple):
    name: str
    value: Optional[str]  # None means boolean attribute
    quote: Optional[str]  # '"' or "'" if quoted


class TagToken(NamedTuple):
    name: str
    is_close: bool
    is_self: bool
    start: int
    end: int
    attrs: Tuple[AttrToken, ...]


# Allow dot in tag names so <item.icon> stays a single tag token.
# This prevents ".icon" being mis-parsed as an attribute.
_TAGNAME_CHARS = set("._-:")  # plus alnum


def _is_tagname_char(c: str) -> bool:
    return c.isalnum() or c in _TAGNAME_CHARS


def _escape_quotes_in_braced_attr_values(html: str) -> str:
    """Make JSX-like braced expressions inside quoted attributes HTML-safe.

    Example (invalid HTML):
        class="{isOpen ? "a" : "b"}"

    Becomes (valid HTML):
        class="{isOpen ? &quot;a&quot; : &quot;b&quot;}"
    """
    out: list[str] = []
    i = 0
    n = len(html)

    while i < n:
        # Detect: ="{...}" or ='{...}'
        if (
            html[i] == "="
            and i + 2 < n
            and html[i + 1] in ('"', "'")
            and html[i + 2] == "{"
        ):
            quote = html[i + 1]
            out.append("=")
            out.append(quote)

            k = i + 2
            brace_depth = 0
            in_str: Optional[str] = None
            esc = False
            expr_out: list[str] = []

            while k < n:
                c = html[k]

                # Escape the delimiter quote inside the braced expression
                if c == quote:
                    expr_out.append("&quot;" if quote == '"' else "&#39;")
                else:
                    expr_out.append(c)

                # Track JS-like strings; braces inside strings do not change brace_depth
                if esc:
                    esc = False
                else:
                    if in_str is not None:
                        if c == "\\":
                            esc = True
                        elif c == in_str:
                            in_str = None
                    else:
                        if c in ("'", '"'):
                            in_str = c
                        elif c == "{":
                            brace_depth += 1
                        elif c == "}":
                            brace_depth -= 1
                            if brace_depth == 0:
                                k += 1
                                break

                k += 1

            # Malformed input: fall back to raw remainder
            if brace_depth != 0:
                out.append(html[i + 2:])
                break

            out.append("".join(expr_out))

            # Keep closing quote if present
            if k < n and html[k] == quote:
                out.append(quote)
                k += 1

            i = k
            continue

        out.append(html[i])
        i += 1

    return "".join(out)


def _iter_tag_tokens(html: str) -> Iterator[TagToken]:
    """Tokenize tags in an HTML-like string without lowercasing.

    - Preserves tag name case (critical for JSX-style components).
    - Skips comments and doctypes.
    - Respects quotes inside tags so '>' in attributes won't terminate early.

    NOTE: Supports dots in tag names so patterns like <item.icon /> remain intact.
    """
    n = len(html)
    i = 0

    while i < n:
        lt = html.find('<', i)
        if lt == -1:
            return

        # Comment
        if html.startswith('<!--', lt):
            end = html.find('-->', lt)
            i = (end + 3) if end != -1 else n
            continue

        # Doctype / processing instruction / other declarations
        if html.startswith('<!', lt) or html.startswith('<?', lt):
            end = html.find('>', lt)
            i = (end + 1) if end != -1 else n
            continue

        # Closing tag
        if html.startswith('</', lt):
            j = lt + 2
            while j < n and _is_tagname_char(html[j]):
                j += 1
            name = html[lt + 2: j]
            end = html.find('>', j)
            if not name or end == -1:
                i = lt + 1
                continue
            yield TagToken(name=name, is_close=True, is_self=False, start=lt, end=end + 1, attrs=())
            i = end + 1
            continue

        # Opening / self-closing tag
        j = lt + 1
        if j >= n or not (html[j].isalpha() or html[j] in '_'):
            i = lt + 1
            continue

        while j < n and _is_tagname_char(html[j]):
            j += 1
        name = html[lt + 1: j]
        if not name:
            i = lt + 1
            continue

        # Parse until matching '>' respecting quotes
        in_dq = False
        in_sq = False
        k = j
        while k < n:
            c = html[k]
            if in_dq:
                if c == '"':
                    in_dq = False
            elif in_sq:
                if c == "'":
                    in_sq = False
            else:
                if c == '"':
                    in_dq = True
                elif c == "'":
                    in_sq = True
                elif c == '>':
                    raw_inside = html[j:k]
                    is_self = raw_inside.rstrip().endswith('/')
                    attrs_str = raw_inside[:-1] if is_self else raw_inside
                    attrs = tuple(_parse_attributes(attrs_str))
                    yield TagToken(name=name, is_close=False, is_self=is_self, start=lt, end=k + 1, attrs=attrs)
                    i = k + 1
                    break
            k += 1
        else:
            i = lt + 1


def _parse_attributes(attrs_str: str) -> List[AttrToken]:
    """Parse attributes from a tag's inside text (between tag name and '>').

    Supports:
      - key="value" / key='value'
      - key=value (unquoted)
      - boolean attrs: key
    """
    s = attrs_str
    n = len(s)
    i = 0
    out: List[AttrToken] = []

    while i < n:
        # Skip whitespace
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            break

        # Read attribute name
        start = i
        while i < n and not s[i].isspace() and s[i] not in ('=', '/', '>'):
            i += 1
        name = s[start:i]
        if not name:
            i += 1
            continue

        # Skip whitespace
        while i < n and s[i].isspace():
            i += 1

        # Boolean attribute
        if i >= n or s[i] != '=':
            out.append(AttrToken(name=name, value=None, quote=None))
            continue

        # '=' then value
        i += 1
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            out.append(AttrToken(name=name, value='', quote=None))
            break

        q = None
        if s[i] in ('"', "'"):
            q = s[i]
            i += 1
            v_start = i
            while i < n and s[i] != q:
                i += 1
            value = s[v_start:i]
            if i < n and s[i] == q:
                i += 1
            out.append(AttrToken(name=name, value=value, quote=q))
        else:
            v_start = i
            while i < n and not s[i].isspace() and s[i] not in ('>',):
                i += 1
            value = s[v_start:i]
            out.append(AttrToken(name=name, value=value, quote=None))

    return out


def _rebuild_open_tag(name: str, attrs: Tuple[AttrToken, ...], is_self: bool) -> str:
    parts = [f"<{name}"]

    for a in attrs:
        out_name = camel_to_kebab(a.name) if (
            a.value is not None and has_mustache(a.value)) else a.name

        if a.value is None:
            parts.append(out_name)
            continue

        if a.quote == '"':
            parts.append(f'{out_name}="{a.value}"')
        elif a.quote == "'":
            parts.append(f"{out_name}='{a.value}'")
        else:
            parts.append(f"{out_name}={a.value}")

    if is_self:
        return (parts[0] + (" " + " ".join(parts[1:]) if len(parts) > 1 else "") + " />")

    return (parts[0] + (" " + " ".join(parts[1:]) if len(parts) > 1 else "") + ">")


def _rewrite_dynamic_attr_names(html: str) -> str:
    tokens = list(_iter_tag_tokens(html))
    if not tokens:
        return html

    out = html
    for t in sorted(tokens, key=lambda x: x.start, reverse=True):
        if t.is_close:
            continue
        rebuilt = _rebuild_open_tag(t.name, t.attrs, t.is_self)
        out = out[: t.start] + rebuilt + out[t.end:]

    return out


def _find_first_component_occurrence(html: str, merged_map: Dict[str, Component]) -> Optional[Tuple[TagToken, Optional[TagToken]]]:
    tokens = list(_iter_tag_tokens(html))

    for idx, t in enumerate(tokens):
        if t.is_close:
            continue

        # Components must start with uppercase like JSX.
        # This will automatically skip <item.icon> and any lowercase dynamic tag.
        if not t.name or not t.name[0].isupper():
            continue

        if t.name not in merged_map:
            continue

        if t.is_self:
            return t, None

        depth = 1
        for j in range(idx + 1, len(tokens)):
            tt = tokens[j]
            if not tt.name or tt.name != t.name:
                continue
            if not tt.is_close and not tt.is_self:
                depth += 1
            elif tt.is_close:
                depth -= 1
                if depth == 0:
                    return t, tt

        return t, None

    return None


# ============================================================================
# HELPER: Mustache & Attributes
# ============================================================================

def convert_mustache_attrs_to_kebab_raw(html: str) -> str:
    html = _escape_quotes_in_braced_attr_values(str(html))
    return _rewrite_dynamic_attr_names(html)


# ============================================================================
# IMPORT PARSING
# ============================================================================

def extract_imports(html: str) -> List[Dict]:
    imports = []

    grouped_pattern = r'<!--\s*@import\s*\{([^}]+)\}\s*from\s*["\']?([^"\'>\s]+)["\']?\s*-->'
    grouped_re = re.compile(grouped_pattern)
    for match in grouped_re.finditer(html):
        try:
            members = match.group(1)
            path = match.group(2)
        except IndexError:
            continue

        for member in members.split(','):
            member = member.strip()
            if not member:
                continue
            if ' as ' in member:
                parts = member.split(' as ')
                original = parts[0].strip()
                alias = parts[1].strip()
            else:
                original = member
                alias = member
            imports.append(
                {'original': original, 'alias': alias, 'path': path})

    single_pattern = r'<!--\s*@import\s+(?!\{)(\w+)(?:\s+as\s+(\w+))?\s+from\s*["\']?([^"\'>\s]+)["\']?\s*-->'
    single_re = re.compile(single_pattern)
    for match in single_re.finditer(html):
        try:
            original = match.group(1)
            alias = match.group(2) or original
            path = match.group(3)
        except IndexError:
            continue
        imports.append({'original': original, 'alias': alias, 'path': path})

    return imports


def strip_imports(html: str) -> str:
    html = re.sub(
        r'<!--\s*@import\s*\{[^}]+\}\s*from\s*["\']?[^"\'>\s]+["\']?\s*-->\n?', '', html
    )
    html = re.sub(
        r'<!--\s*@import\s+\w+(?:\s+as\s+\w+)?\s+from\s*["\']?[^"\'>\s]+["\']?\s*-->\n?', '', html
    )
    return html


def build_alias_map(imports: List[Dict], base_dir: str = "") -> Dict[str, Component]:
    alias_map: Dict[str, Component] = {}
    for imp in imports:
        comp = load_component_from_path(imp['path'], imp['original'], base_dir)
        if comp:
            alias_map[imp['alias']] = comp
    return alias_map


def process_imports(html: str, base_dir: str = "") -> tuple[str, Dict[str, Component]]:
    imports = extract_imports(html)
    alias_map = build_alias_map(imports, base_dir)
    cleaned_html = strip_imports(html)
    return cleaned_html, alias_map


# ============================================================================
# COMPONENT HELPERS
# ============================================================================

def needs_parent_scope(attrs):
    for key, value in attrs.items():
        if key.lower().startswith('on'):
            return True
        if has_mustache(value):
            return True
    return False


def wrap_scope(html, scope):
    return f'<!-- pp-scope:{scope} -->{html}<!-- /pp-scope -->'


def accepts_children(fn):
    sig = fn.__signature__ if isinstance(
        fn, Component) else inspect.signature(fn)
    params = sig.parameters
    return 'children' in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())


def _event_listener_props(props: Dict[str, str]) -> Dict[str, str]:
    return {k: v for k, v in props.items() if k.lower().startswith("on")}


def _event_attr_names(event_prop: str) -> Tuple[str, str]:
    return event_prop, camel_to_kebab(event_prop)


_RAWTEXT_ROOT_TAGS = {"textarea", "title"}


def _inject_component_scope_inside_root(html: str, component_scope: str) -> str:
    s = str(html).strip()
    if not s:
        return s

    tag_name, _, is_self_closing, end_pos = _scan_opening_tag(s, 0)
    if not tag_name:
        return wrap_scope(s, component_scope)

    if tag_name.lower() in _RAWTEXT_ROOT_TAGS or is_self_closing:
        return wrap_scope(s, component_scope)

    close_start = _scan_closing_tag(s, tag_name, end_pos)
    if close_start == -1:
        return wrap_scope(s, component_scope)

    return s[:end_pos] + f"<!-- pp-scope:{component_scope} -->" + s[end_pos:close_start] + "<!-- /pp-scope -->" + s[close_start:]


def _wrap_event_elements_with_parent_scope(html: str, event_listeners: Dict[str, str], parent_scope: str) -> str:
    if not event_listeners or not parent_scope:
        return str(html)
    s = str(html)
    wraps: List[Tuple[int, int, str]] = []

    for event_prop, handler in event_listeners.items():
        _, kebab_name = _event_attr_names(event_prop)
        camel_name = event_prop

        attr_pat = re.compile(
            rf"<([a-zA-Z][\w:-]*)\b[^>]*\s(?:{re.escape(camel_name)}|{re.escape(kebab_name)})\s*=\s*(\"([^\"]*)\"|'([^']*)')[^>]*>",
            re.IGNORECASE,
        )

        for m in attr_pat.finditer(s):
            val = m.group(3) if m.group(3) is not None else (m.group(4) or "")
            if val != handler:
                continue

            tag = m.group(1)
            start = m.start()
            _, _, is_self, open_end = _scan_opening_tag(s, start)

            if is_self:
                wraps.append((start, open_end, wrap_scope(
                    s[start:open_end], parent_scope)))
                continue

            close_start = _scan_closing_tag(s, tag, open_end)
            if close_start == -1:
                continue

            close_end = s.find(">", close_start) + 1
            if close_end == 0:
                continue

            wraps.append((start, close_end, wrap_scope(
                s[start:close_end], parent_scope)))

    if not wraps:
        return s

    for start, end, repl in sorted(wraps, key=lambda x: x[0], reverse=True):
        s = s[:start] + repl + s[end:]

    return s


def _get_root_tag_name(fragment: str) -> str:
    tag, _, _, _ = _scan_opening_tag(str(fragment).strip(), 0)
    return tag.lower() if tag else ""


# ============================================================================
# ROBUST PARSING (FIXED LOGIC)
# ============================================================================

def _scan_opening_tag(html: str, start_pos: int) -> Tuple[Optional[str], str, bool, int]:
    length = len(html)
    if start_pos >= length or html[start_pos] != '<':
        return None, "", False, start_pos

    i = start_pos + 1
    while i < length and _is_tagname_char(html[i]):
        i += 1

    tag_name = html[start_pos+1:i]
    if not tag_name:
        return None, "", False, start_pos

    in_dquote = False
    in_squote = False
    attrs_start = i

    while i < length:
        char = html[i]

        if in_dquote:
            if char == '"':
                in_dquote = False
        elif in_squote:
            if char == "'":
                in_squote = False
        else:
            if char == '"':
                in_dquote = True
            elif char == "'":
                in_squote = True
            elif char == '>':
                is_self_closing = (html[i-1] == '/')
                attrs_end = i - 1 if is_self_closing else i
                attrs_str = html[attrs_start:attrs_end]
                return tag_name, attrs_str, is_self_closing, i + 1
        i += 1

    return None, "", False, start_pos


def _scan_closing_tag(html: str, tag_name: str, start_pos: int) -> int:
    depth = 1
    length = len(html)
    i = start_pos

    target_close = f"</{tag_name}"
    target_open = f"<{tag_name}"

    while i < length:
        lt = html.find('<', i)
        if lt == -1:
            break

        if html.startswith(target_close, lt):
            after = lt + len(target_close)
            if after < length and html[after] in '> \t\n\r':
                depth -= 1
                if depth == 0:
                    return lt
                i = html.find('>', after) + 1
                continue

        if html.startswith(target_open, lt):
            after = lt + len(target_open)
            if after < length and html[after] in '> \t\n\r/':
                _, _, is_self, end_nested = _scan_opening_tag(html, lt)
                if not is_self:
                    depth += 1
                i = end_nested
                continue

        if html.startswith("<!--", lt):
            end_comment = html.find("-->", lt)
            if end_comment != -1:
                i = end_comment + 3
                continue

        if lt + 1 < length and (html[lt+1].isalnum() or html[lt+1] == '/'):
            _, _, _, end_other = _scan_opening_tag(html, lt)
            i = end_other if end_other > lt else lt + 1
        else:
            i = lt + 1

    return -1


# ============================================================================
# RAW BLOCK PROTECTION
# ============================================================================

_RAW_TAGS_DEFAULT = ("script", "style")


def _mask_raw_blocks(html: str, tags: Tuple[str, ...] = _RAW_TAGS_DEFAULT) -> Tuple[str, List[Tuple[str, str]]]:
    blocks: List[Tuple[str, str]] = []
    for tag in tags:
        pattern = re.compile(
            rf'<{tag}\b[^>]*>[\s\S]*?</{tag}\s*>', re.IGNORECASE)

        def repl(m):
            token = f"__PP_RAW_{tag.upper()}_{uuid.uuid4().hex}__"
            blocks.append((token, m.group(0)))
            return token

        html = pattern.sub(repl, html)
    return html, blocks


def _unmask_raw_blocks(html: str, blocks: List[Tuple[str, str]]) -> str:
    for token, original in blocks:
        html = html.replace(token, original)
    return html


# ============================================================================
# MAIN TRANSFORM
# ============================================================================

def transform_components(
    html: str,
    parent_scope: str = "app",
    base_dir: str = "",
    alias_map: Optional[Dict[str, Component]] = None,
    _depth: int = 0
) -> str:
    if _depth > 50:
        return html

    html, raw_blocks = _mask_raw_blocks(html)

    html, local_alias_map = process_imports(html, base_dir)
    merged_map = {**(alias_map or {}), **local_alias_map}

    if not merged_map:
        return _unmask_raw_blocks(html, raw_blocks)

    html = convert_mustache_attrs_to_kebab_raw(html)

    candidate_pattern = re.compile(r'<([A-Z][a-zA-Z0-9\.\_\-\:]*)')

    max_iterations = 100
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        best_match = None
        for m in candidate_pattern.finditer(html):
            name = m.group(1)
            if name in merged_map:
                best_match = m
                break

        if not best_match:
            break

        found_start = best_match.start()
        found_tag_name = best_match.group(1)
        component_fn = merged_map[found_tag_name]

        tag_name, attrs_str, is_self_closing, open_end = _scan_opening_tag(
            html, found_start)

        if not tag_name or tag_name != found_tag_name:
            html = html[:found_start] + "__SKIP__" + html[found_start+1:]
            continue

        children_html = ""
        full_end = open_end

        if not is_self_closing:
            close_start = _scan_closing_tag(html, tag_name, open_end)
            if close_start != -1:
                children_html = html[open_end:close_start]
                close_tag_end = html.find('>', close_start) + 1
                full_end = close_tag_end
            else:
                print(
                    f"[Caspian] Warning: Unclosed component <{tag_name}> found.")
                break

        attr_tokens = _parse_attributes(attrs_str)
        props: Dict[str, str] = {}

        for token in attr_tokens:
            camel = kebab_to_camel(token.name)
            if token.value is None:
                if camel not in props:
                    props[camel] = ""
            else:
                props[camel] = token.value

        unique_id = f"{tag_name.lower()}_{uuid.uuid4().hex[:8]}"

        if children_html and accepts_children(component_fn):
            props['children'] = wrap_scope(children_html, parent_scope)

        try:
            component_html = component_fn(**props)
        except Exception as e:
            print(f"[Caspian] Error rendering <{tag_name}>: {e}")
            break

        if hasattr(component_fn, 'source_path') and component_fn.source_path:
            component_dir = os.path.dirname(component_fn.source_path)
            component_html = transform_components(
                component_html,
                parent_scope=unique_id,
                base_dir=component_dir,
                _depth=_depth + 1
            )

        component_html = re.sub(
            r'^(\s*<[a-zA-Z][a-zA-Z0-9]*)',
            rf'\1 pp-component="{unique_id}"',
            str(component_html).strip(),
            count=1
        )

        root_tag = _get_root_tag_name(component_html)
        needs_parent = needs_parent_scope(props)
        event_listeners = _event_listener_props(props)

        if root_tag in _RAWTEXT_ROOT_TAGS:
            if needs_parent and parent_scope:
                component_html = wrap_scope(component_html, parent_scope)
            else:
                component_html = wrap_scope(component_html, unique_id)
        else:
            if needs_parent and parent_scope:
                component_html = _inject_component_scope_inside_root(
                    component_html, unique_id)
                if event_listeners:
                    component_html = _wrap_event_elements_with_parent_scope(
                        component_html,
                        event_listeners=event_listeners,
                        parent_scope=parent_scope,
                    )
                component_html = wrap_scope(component_html, parent_scope)
            else:
                component_html = wrap_scope(component_html, unique_id)

        html = html[:found_start] + component_html + html[full_end:]

    html = html.replace("__SKIP__", "<")
    return _unmask_raw_blocks(html, raw_blocks)
