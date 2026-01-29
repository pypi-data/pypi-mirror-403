from __future__ import annotations
import builtins as _builtins
import html
import ipaddress
import json
import mimetypes
import os
import re
import uuid as _uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Any, Iterable, Optional, Protocol, TypeVar, Union, runtime_checkable, cast
import ulid

try:
    # Recommended
    from email_validator import validate_email as _validate_email, EmailNotValidError  # type: ignore
except ImportError:  # pragma: no cover
    _validate_email = None
    EmailNotValidError = Exception

try:
    # Optional (strtotime-like parsing)
    from dateutil.parser import parse as _dateutil_parse  # type: ignore
except ImportError:  # pragma: no cover
    _dateutil_parse = None

try:
    # Optional (real MIME sniffing)
    import magic  # type: ignore
except ImportError:  # pragma: no cover
    magic = None


# Avoid method-name collisions in type positions inside the class.
IntT = _builtins.int
FloatT = _builtins.float
StrT = _builtins.str
TEnum = TypeVar("TEnum", bound=Enum)


@runtime_checkable
class _ReadableSeekable(Protocol):
    def read(self, n: int = ...) -> bytes: ...
    def tell(self) -> int: ...
    def seek(self, offset: int, whence: int = ...) -> int: ...


class Validate:
    # -------------------------
    # Helpers
    # -------------------------

    @staticmethod
    def _php_to_py_format(fmt: str) -> str:
        """
        Minimal PHP date format -> Python strptime/strftime mapping.
        """
        mapping: dict[str, str] = {
            "Y": "%Y",
            "m": "%m",
            "d": "%d",
            "H": "%H",
            "i": "%M",
            "s": "%S",
            "u": "%f",
        }

        out: list[str] = []
        i = 0
        while i < len(fmt):
            ch = fmt[i]
            out.append(mapping.get(ch, ch))
            i += 1
        return "".join(out)

    @staticmethod
    def _is_empty_required(value: Any) -> bool:
        if value == "0":
            return False
        if value is None:
            return True
        if isinstance(value, str):
            return len(value.strip()) == 0
        if isinstance(value, (list, tuple, dict, set)):
            return len(value) == 0
        return False

    @staticmethod
    def _to_str(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)

    @staticmethod
    def _parse_datetime_any(value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        s = str(value).strip()
        if not s:
            return None

        if _dateutil_parse:
            try:
                return _dateutil_parse(s)
            except Exception:
                pass

        # Fallback
        try:
            return datetime.fromisoformat(s)
        except Exception:
            pass

        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                continue

        return None

    # -------------------------
    # String Validation
    # -------------------------

    @staticmethod
    def string(value: Any, escape_html: bool = True) -> str:
        s = Validate._to_str(value).strip()
        return html.escape(s, quote=True) if escape_html else s

    @staticmethod
    def email(value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None

        if _validate_email:
            try:
                _validate_email(s)
                return s
            except EmailNotValidError:
                return None

        # Basic fallback
        return s if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s) else None

    @staticmethod
    def url(value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None
        return s if re.match(r"^(https?://)([^/\s]+)(/.*)?$", s, re.IGNORECASE) else None

    @staticmethod
    def ip(value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        try:
            ipaddress.ip_address(s)
            return s
        except Exception:
            return None

    @staticmethod
    def uuid(value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        try:
            _uuid.UUID(s)
            return s
        except Exception:
            return None

    @staticmethod
    def ulid(value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None
        try:
            ulid.ULID.from_str(s)
            return s
        except Exception:
            return None

    @staticmethod
    def cuid(value: Any) -> Optional[str]:
        return value if isinstance(value, str) and re.fullmatch(r"^c[0-9a-z]{24}$", value) else None

    @staticmethod
    def cuid2(value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        # Strict CUID2 check: lowercase a-z and 0-9 only.
        return value if re.fullmatch(r"^[a-z0-9]{20,}$", value) else None

    @staticmethod
    def nanoid(value: Any, length: int = 21) -> Optional[str]:
        if not isinstance(value, str):
            return None
        regex = f"^[0-9a-zA-Z_-]{{{length}}}$"
        return value if re.fullmatch(regex, value) else None

    @staticmethod
    def bytes(value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        return s if re.fullmatch(r"^[0-9]+[kKmMgGtT]?[bB]?$", s) else None

    @staticmethod
    def xml(value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value)
        return s if re.match(r"^<\?xml", s) else None

    # -------------------------
    # Number Validation
    # -------------------------

    @staticmethod
    def int(value: Any) -> Optional[IntT]:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, _builtins.int):
            return value

        s = str(value).strip()
        if not re.fullmatch(r"[+-]?\d+", s):
            return None
        try:
            return _builtins.int(s)
        except Exception:
            return None

    @staticmethod
    def big_int(value: Any) -> Optional[IntT]:
        return Validate.int(value)

    @staticmethod
    def float(value: Any) -> Optional[FloatT]:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            return None
        try:
            f = _builtins.float(value)
            if f != f:  # NaN
                return None
            return f
        except Exception:
            return None

    @staticmethod
    def decimal(value: Any, scale: _builtins.int = 30) -> Optional[Decimal]:
        if value is None or value == "":
            return None
        try:
            d = Decimal(str(value))
            quant = Decimal("1").scaleb(-scale)
            return d.quantize(quant, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            return None

    # -------------------------
    # Date Validation
    # -------------------------

    @staticmethod
    def date(value: Any, fmt: str = "Y-m-d") -> Optional[str]:
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            dt = value
        else:
            s = str(value)
            py_fmt = Validate._php_to_py_format(fmt)
            try:
                dt = datetime.strptime(s, py_fmt)
            except Exception:
                return None
            if dt.strftime(py_fmt) != s:
                return None

        return dt.strftime(Validate._php_to_py_format(fmt))

    @staticmethod
    def date_time(value: Any, fmt: str = "Y-m-d H:i:s") -> Optional[str]:
        if value is None or value == "":
            return None
        dt = value if isinstance(
            value, datetime) else Validate._parse_datetime_any(value)
        if dt is None:
            return None
        return dt.strftime(Validate._php_to_py_format(fmt))

    # -------------------------
    # Boolean Validation
    # -------------------------

    @staticmethod
    def boolean(value: Any) -> Optional[bool]:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()

        true_set = {"1", "true", "on", "yes", "y"}
        false_set = {"0", "false", "off", "no", "n"}
        if s in true_set:
            return True
        if s in false_set:
            return False
        return None

    # -------------------------
    # Other Validation
    # -------------------------

    @staticmethod
    def json(value: Any) -> str:
        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except Exception as e:
                return str(e)
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def is_json(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        try:
            json.loads(value)
            return True
        except Exception:
            return False

    @staticmethod
    def enum(value: Any, allowed_values: Iterable[Any]) -> bool:
        return value in list(allowed_values)

    @staticmethod
    def enum_class(
        value: Union[str, IntT, TEnum, list[Union[str, IntT, TEnum]]],
        enum_cls: type[Any],
    ) -> Union[str, IntT, list[Union[str, IntT]], None]:
        if not isinstance(enum_cls, type) or not issubclass(enum_cls, Enum):
            raise ValueError(f"'{enum_cls}' is not an Enum class.")

        enum_t = cast(type[Enum], enum_cls)

        def cast_one(v: Any) -> Optional[Union[str, IntT]]:
            if isinstance(v, enum_t):
                return cast(Union[str, IntT], getattr(v, "value", None))
            for member in enum_t:
                if getattr(member, "value", None) == v:
                    return cast(Union[str, IntT], member.value)
            return None

        if isinstance(value, list):
            out: list[Union[str, IntT]] = []
            for item in value:
                c = cast_one(item)
                if c is None:
                    return None
                out.append(c)
            return out

        return cast_one(value)

    @staticmethod
    def emojis(content: str) -> str:
        emoji_map: dict[str, str] = {
            ":)": "😊", ":-)": "😊",
            ":(": "☹️", ":-(": "☹️",
            ":D": "😄", ":-D": "😄",
            ":P": "😛", ":-P": "😛",
            ";)": "😉", ";-)": "😉",
            "<3": "❤️", "</3": "💔",
            ":wave:": "👋",
            ":thumbsup:": "👍",
            ":thumbsdown:": "👎",
            ":fire:": "🔥",
            ":100:": "💯",
            ":poop:": "💩",
        }
        for k in sorted(emoji_map.keys(), key=len, reverse=True):
            content = content.replace(k, emoji_map[k])
        return content

    # -------------------------
    # Rules Engine
    # -------------------------

    @staticmethod
    def with_rules(
        value: Any,
        rules: Union[str, list[str]],
        confirmation_value: Any = None
    ) -> Union[bool, str, None]:

        if isinstance(rules, list):
            rules_array = rules
        else:
            rules_array = rules.split("|") if rules else []

        for rule in rules_array:
            if ":" in rule:
                rule_name, parameter = rule.split(":", 1)
                result = Validate.apply_rule(
                    rule_name, parameter, value, confirmation_value)
            else:
                result = Validate.apply_rule(
                    rule, None, value, confirmation_value)

            if result is not True:
                return result
        return True

    @staticmethod
    def apply_rule(rule: str, parameter: Optional[str], value: Any, confirmation_value: Any = None) -> Union[bool, str]:
        s = "" if value is None else str(value)

        if rule == "required":
            return True if not Validate._is_empty_required(value) else "This field is required."

        if rule == "min":
            n = _builtins.int(parameter or "0")
            return True if len(s) >= n else f"This field must be at least {n} characters long."

        if rule == "max":
            n = _builtins.int(parameter or "0")
            return True if len(s) <= n else f"This field must not exceed {n} characters."

        if rule == "startsWith":
            p = parameter or ""
            return True if s.startswith(p) else f"This field must start with {p}."

        if rule == "endsWith":
            p = parameter or ""
            return True if s.endswith(p) else f"This field must end with {p}."

        if rule == "confirmed":
            return True if confirmation_value == value else f"The {rule} confirmation does not match."

        if rule == "email":
            return True if Validate.email(value) else "This field must be a valid email address."

        if rule == "url":
            return True if Validate.url(value) else "This field must be a valid URL."

        if rule == "ip":
            return True if Validate.ip(value) else "This field must be a valid IP address."

        if rule == "uuid":
            return True if Validate.uuid(value) else "This field must be a valid UUID."

        if rule == "ulid":
            return True if Validate.ulid(value) else "This field must be a valid ULID."

        if rule == "cuid":
            return True if Validate.cuid(value) else "This field must be a valid CUID."

        if rule == "cuid2":
            return True if Validate.cuid2(value) else "This field must be a valid CUID2."

        if rule == "nanoid":
            return True if Validate.nanoid(value) else "This field must be a valid NanoID."

        if rule == "int":
            return True if Validate.int(value) is not None else "This field must be an integer."

        if rule == "float":
            return True if Validate.float(value) is not None else "This field must be a float."

        if rule == "boolean":
            return True if Validate.boolean(value) is not None else "This field must be a boolean."

        if rule == "in":
            opts = [x.strip()
                    for x in (parameter or "").split(",") if x.strip() != ""]
            return True if s in opts else "The selected value is invalid."

        if rule == "notIn":
            opts = [x.strip()
                    for x in (parameter or "").split(",") if x.strip() != ""]
            return True if s not in opts else "The selected value is invalid."

        if rule == "size":
            n = _builtins.int(parameter or "0")
            return True if len(s) == n else f"This field must be exactly {n} characters long."

        if rule == "between":
            parts = (parameter or "").split(",", 1)
            if len(parts) != 2:
                return "This field has an invalid between rule."
            mn, mx = _builtins.int(parts[0]), _builtins.int(parts[1])
            return True if (mn <= len(s) <= mx) else f"This field must be between {mn} and {mx} characters long."

        if rule == "date":
            fmt = parameter or "Y-m-d"
            return True if Validate.date(value, fmt) else "This field must be a valid date."

        if rule == "dateFormat":
            if not parameter:
                return "This field has an invalid dateFormat rule."
            py_fmt = Validate._php_to_py_format(parameter)
            try:
                datetime.strptime(s, py_fmt)
                return True
            except Exception:
                return f"This field must match the format {parameter}."

        if rule == "before":
            left = Validate._parse_datetime_any(value)
            right = Validate._parse_datetime_any(parameter)
            if left is None or right is None:
                return f"This field must be a date before {parameter}."
            return True if left < right else f"This field must be a date before {parameter}."

        if rule == "after":
            left = Validate._parse_datetime_any(value)
            right = Validate._parse_datetime_any(parameter)
            if left is None or right is None:
                return f"This field must be a date after {parameter}."
            return True if left > right else f"This field must be a date after {parameter}."

        if rule == "json":
            return True if Validate.is_json(value) else "This field must be a valid JSON string."

        if rule == "regex":
            if not parameter:
                return "This field format is invalid."
            try:
                return True if re.search(parameter, s) else "This field format is invalid."
            except re.error:
                return "This field format is invalid."

        if rule == "digits":
            n = _builtins.int(parameter or "0")
            return True if s.isdigit() and len(s) == n else f"This field must be {n} digits."

        if rule == "digitsBetween":
            parts = (parameter or "").split(",", 1)
            if len(parts) != 2:
                return "This field has an invalid digitsBetween rule."
            mn, mx = _builtins.int(parts[0]), _builtins.int(parts[1])
            return True if s.isdigit() and (mn <= len(s) <= mx) else f"This field must be between {mn} and {mx} digits."

        if rule == "extensions":
            exts = [x.strip()
                    for x in (parameter or "").split(",") if x.strip()]
            return True if Validate.is_extension_allowed(value, exts) else (
                "The file must have one of the following extensions: " +
                ", ".join(exts) + "."
            )

        if rule == "mimes":
            mimes_ = [x.strip()
                      for x in (parameter or "").split(",") if x.strip()]
            return True if Validate.is_mime_type_allowed(value, mimes_) else (
                "The file must be of type: " + ", ".join(mimes_) + "."
            )

        if rule == "file":
            return True if Validate.is_file(value) else "This field must be a valid file."

        return True

    # -------------------------
    # File helpers
    # -------------------------

    @staticmethod
    def is_file(file_value: Any) -> bool:
        if isinstance(file_value, str):
            return os.path.isfile(file_value)
        return isinstance(file_value, _ReadableSeekable) or hasattr(file_value, "read")

    @staticmethod
    def is_extension_allowed(file_value: Any, allowed_extensions: list[str]) -> bool:
        filename: Optional[str] = None

        if isinstance(file_value, str):
            filename = file_value
        elif hasattr(file_value, "filename"):
            maybe = getattr(file_value, "filename")
            if isinstance(maybe, str):
                filename = maybe

        if not filename:
            return False

        ext = os.path.splitext(filename)[1].lstrip(".").lower()
        allowed = {e.lower().lstrip(".") for e in allowed_extensions}
        return ext in allowed

    @staticmethod
    def is_mime_type_allowed(file_value: Any, allowed_mime_types: list[str]) -> bool:
        # Real sniffing first
        if magic is not None:
            try:
                if isinstance(file_value, str) and os.path.isfile(file_value):
                    mt = magic.from_file(file_value, mime=True)
                    return mt in allowed_mime_types

                if isinstance(file_value, _ReadableSeekable):
                    pos = file_value.tell()
                    data = file_value.read(2048)
                    file_value.seek(pos)
                    mt = magic.from_buffer(data, mime=True)
                    return mt in allowed_mime_types
            except Exception:
                pass

        # Fallback: mimetypes guess by filename
        filename: Optional[str] = None
        if isinstance(file_value, str):
            filename = file_value
        elif hasattr(file_value, "filename"):
            maybe = getattr(file_value, "filename")
            if isinstance(maybe, str):
                filename = maybe

        if not filename:
            return False

        guessed, _ = mimetypes.guess_type(filename)
        return guessed in allowed_mime_types


class Rule:
    """
    IntelliSense helper for Validation rules.
    Usage: Validate.with_rules(val, [Rule.required, Rule.min(5)])
    """
    # Simple Rules (Constants)
    REQUIRED = "required"
    EMAIL = "email"
    URL = "url"
    IP = "ip"
    UUID = "uuid"
    ULID = "ulid"
    CUID = "cuid"
    CUID2 = "cuid2"
    NANOID = "nanoid"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    FILE = "file"

    # Parameterized Rules (Methods)
    @staticmethod
    def min(value: int) -> str:
        return f"min:{value}"

    @staticmethod
    def max(value: int) -> str:
        return f"max:{value}"

    @staticmethod
    def size(value: int) -> str:
        return f"size:{value}"

    @staticmethod
    def starts_with(prefix: str) -> str:
        return f"startsWith:{prefix}"

    @staticmethod
    def ends_with(suffix: str) -> str:
        return f"endsWith:{suffix}"

    @staticmethod
    def confirmed() -> str:
        return "confirmed"

    @staticmethod
    def in_list(values: list[Any]) -> str:
        # joing values with comma
        val_str = ",".join(str(v) for v in values)
        return f"in:{val_str}"

    @staticmethod
    def not_in_list(values: list[Any]) -> str:
        val_str = ",".join(str(v) for v in values)
        return f"notIn:{val_str}"

    @staticmethod
    def between(min_val: int, max_val: int) -> str:
        return f"between:{min_val},{max_val}"

    @staticmethod
    def digits(count: int) -> str:
        return f"digits:{count}"

    @staticmethod
    def digits_between(min_val: int, max_val: int) -> str:
        return f"digitsBetween:{min_val},{max_val}"

    @staticmethod
    def date(fmt: str = "Y-m-d") -> str:
        return f"date:{fmt}"

    @staticmethod
    def date_format(fmt: str) -> str:
        return f"dateFormat:{fmt}"

    @staticmethod
    def before(date_str: str) -> str:
        return f"before:{date_str}"

    @staticmethod
    def after(date_str: str) -> str:
        return f"after:{date_str}"

    @staticmethod
    def regex(pattern: str) -> str:
        return f"regex:{pattern}"

    @staticmethod
    def extensions(exts: list[str]) -> str:
        return f"extensions:{','.join(exts)}"

    @staticmethod
    def mimes(types: list[str]) -> str:
        return f"mimes:{','.join(types)}"
