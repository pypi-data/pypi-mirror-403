import re
from typing import List, Tuple, Dict, Optional, Any
from casp.string_helpers import kebab_to_camel


class CaspianParser:
    """
    A robust, stack-based parser for Caspian Syntax.
    Handles nesting, attributes with special characters, and self-closing tags correctly.
    """

    def __init__(self):
        self.source = ""
        self.length = 0
        self.pos = 0
        self.output = []
        # Stack stores tuples: (block_type, context_info)
        # block_type: 'dynamic', 'for', 'if', 'else', 'elif'
        self.stack: List[Tuple[str, Any]] = []

    def feed(self, content: str):
        self.source = content
        self.length = len(content)
        self.pos = 0
        self.output = []
        self.stack = []

        while self.pos < self.length:
            # Efficiently scan for the next '<' character
            next_lt = self.source.find('<', self.pos)

            if next_lt == -1:
                # No more tags, flush remaining text
                self.output.append(self.source[self.pos:])
                self.pos = self.length
                break

            # Append text preceding the tag
            if next_lt > self.pos:
                self.output.append(self.source[self.pos:next_lt])

            self.pos = next_lt

            # Attempt to match specific Caspian tags
            # Order matters: check strictly specific syntax first
            if self._handle_dynamic_open():
                continue
            if self._handle_dynamic_close():
                continue
            if self._handle_template_open():
                continue
            if self._handle_template_close():
                continue

            # If no Caspian tag matched, treat '<' as literal text and advance
            self.output.append('<')
            self.pos += 1

    def get_result(self) -> str:
        return "".join(self.output)

    # --- Matchers & Handlers ---

    def _handle_dynamic_open(self) -> bool:
        """
        Matches <[[ expression ]] attributes ... >
        """
        # 1. Check for opening sequence <[[
        if not self.source.startswith('<[[', self.pos):
            return False

        # 2. Extract the expression inside [[ ... ]]
        # We look for the closing ]] that ends the expression part
        expr_end = self.source.find(']]', self.pos)
        if expr_end == -1:
            return False  # Malformed

        expr_start = self.pos + 3  # Skip <[[
        expression = self.source[expr_start:expr_end].strip()

        expression = sanitize_jinja_expression(expression)

        # 3. Parse attributes after the ]] but before > or />
        # Start scanning for attributes after the expression's ]]
        scan_pos = expr_end + 2

        attrs_str, end_pos, is_self_closing = self._extract_attributes_and_end(
            scan_pos)
        if end_pos == -1:
            return False  # Malformed tag structure

        # 4. Convert Attributes
        props = parse_attrs_to_dict_str(attrs_str)

        # 5. Output Logic
        if is_self_closing:
            # Case: <[[ expr ]] /> -> [[ render_dynamic(expr, props) ]]
            self.output.append(f"[[ render_dynamic({expression}, {props}) ]]")
        else:
            # Case: <[[ expr ]] > ... </[[ expr ]]>
            self.output.append(
                f"[% call(content) render_dynamic({expression}, {props}) %]")
            self.stack.append(('dynamic', expression))

        self.pos = end_pos
        return True

    def _handle_dynamic_close(self) -> bool:
        """
        Matches </[[ ... ]]>
        """
        if not self.source.startswith('</[[', self.pos):
            return False

        # Find the end of the tag
        tag_end = self.source.find('>', self.pos)
        if tag_end == -1:
            return False

        if self.stack and self.stack[-1][0] == 'dynamic':
            self.stack.pop()
            self.output.append("[% endcall %]")
        else:
            pass

        self.pos = tag_end + 1
        return True

    def _handle_template_open(self) -> bool:
        """
        Matches <template casp-action="...">
        """
        if not self.source.startswith('<template', self.pos):
            return False

        after_tag = self.pos + 9  # len('<template')
        if after_tag < self.length and self.source[after_tag].isalnum():
            return False

        attrs_str, end_pos, is_self_closing = self._extract_attributes_and_end(
            after_tag)
        if end_pos == -1:
            return False

        attrs = self._parse_attrs_to_dict(attrs_str)

        casp_action = None
        casp_value = None

        for key, value in attrs.items():
            if key.startswith('casp-'):
                casp_action = key
                casp_value = value
                break

        if not casp_action:
            return False

        if casp_value:
            casp_value = sanitize_jinja_expression(casp_value)

        if casp_action == 'casp-for':
            self.output.append(f"[% for {casp_value} %]")
            self.stack.append(('for', None))
        elif casp_action == 'casp-if':
            self.output.append(f"[% if {casp_value} %]")
            self.stack.append(('if', None))
        elif casp_action == 'casp-elif':
            self.output.append(f"[% elif {casp_value} %]")
            self.stack.append(('elif', None))
        elif casp_action == 'casp-else':
            self.output.append(f"[% else %]")
            self.stack.append(('else', None))

        self.pos = end_pos
        return True

    def _handle_template_close(self) -> bool:
        """
        Matches </template>
        """
        if not self.source.startswith('</template>', self.pos):
            return False

        if self.stack:
            block_type, _ = self.stack[-1]

            if block_type == 'for':
                self.output.append("[% endfor %]")
                self.stack.pop()
                self.pos += 11  # len('</template>')
                return True

            elif block_type == 'if':
                self.output.append("[% endif %]")
                self.stack.pop()
                self.pos += 11
                return True

            elif block_type in ('elif', 'else'):
                self.output.append("[% endif %]")
                self.stack.pop()
                self.pos += 11
                return True

        return False

    def _extract_attributes_and_end(self, start_pos: int) -> Tuple[str, int, bool]:
        cursor = start_pos
        in_quote = False
        quote_char = ''

        while cursor < self.length:
            char = self.source[cursor]

            if in_quote:
                if char == quote_char:
                    if self.source[cursor-1] != '\\':
                        in_quote = False
            else:
                if char in ('"', "'"):
                    in_quote = True
                    quote_char = char
                elif char == '>':
                    if self.source[cursor-1] == '/':
                        return self.source[start_pos:cursor-1], cursor + 1, True
                    return self.source[start_pos:cursor], cursor + 1, False

            cursor += 1

        return "", -1, False

    def _parse_attrs_to_dict(self, attrs_str: str) -> Dict[str, str]:
        attrs = {}
        pattern = r'([a-zA-Z0-9_-]+)(?:=(?:"([^"]*)"|\'([^\']*)\'|(\S+)))?'
        for match in re.finditer(pattern, attrs_str):
            key = match.group(1)
            val = match.group(2) or match.group(3) or match.group(4) or ""
            attrs[key] = val
        return attrs


def transpile_syntax(html: str) -> str:
    parser = CaspianParser()
    parser.feed(html)
    return parser.get_result()


def sanitize_jinja_expression(expr: str) -> str:
    """
    Auto-fixes common dictionary method conflicts in dot notation.
    Translates: menu.items -> menu['items']
    Ignores:    menu.items() (actual method calls)
    """
    # List of common dict methods that conflict with common variable names
    reserved = ['items', 'values', 'keys', 'update', 'pop', 'get']

    for word in reserved:
        # Match .word at a word boundary, NOT followed by (
        # Example matches: "menu.items", "menu.items "
        # Example ignores: "menu.items()"
        pattern = r'\.' + word + r'\b(?!\()'
        expr = re.sub(pattern, f"['{word}']", expr)

    return expr


def parse_attrs_to_dict_str(attrs_str: str) -> str:
    """
    Parses HTML-like attributes into a Python dict string.
    Correctly handles 'class' -> 'class_name' and boolean attributes.
    """
    if not attrs_str:
        return "{}"

    props = []
    # Matches key="val", key='val', or key=[[expr]]
    attr_pattern = r'([a-zA-Z0-9_-]+)(?:=(?:"([^"]*)"|\'([^\']*)\'|\[\[([^\]]+)\]\]))?'

    # Track which keys we've seen to handle boolean attributes vs value attributes
    seen_keys = set()

    for match in re.finditer(attr_pattern, attrs_str):
        key = match.group(1)
        val_double = match.group(2)
        val_single = match.group(3)
        val_expr = match.group(4)

        py_key = kebab_to_camel(key)

        # Handle Python reserved keywords
        if py_key == "className":
            py_key = "class_name"
        if py_key == "htmlFor":
            py_key = "html_for"
        if py_key == "class":
            py_key = "class_name"
        if py_key == "for":
            py_key = "html_for"

        seen_keys.add(key)

        if val_expr:
            # === FIX: Sanitize Props Expressions too ===
            sanitized_expr = sanitize_jinja_expression(val_expr.strip())
            props.append(f'"{py_key}": {sanitized_expr}')
        elif val_double is not None:
            props.append(f'"{py_key}": "{val_double}"')
        elif val_single is not None:
            props.append(f'"{py_key}": "{val_single}"')
        else:
            props.append(f'"{py_key}": True')

    return "{" + ", ".join(props) + "}"
