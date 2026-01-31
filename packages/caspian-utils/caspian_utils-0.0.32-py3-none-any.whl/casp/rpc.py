import traceback
from datetime import timedelta
from .auth import auth
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from functools import wraps
from .caspian_config import get_files_index
from typing import Optional, Any, Union
import inspect
import os
import json
import hmac
import dataclasses
from datetime import datetime, date
import time
from collections import defaultdict
import re
import math
from .streaming import SSE

RPC_REGISTRY = {}
RPC_META = {}

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(
    ',') if os.getenv('CORS_ALLOWED_ORIGINS') else None
IS_PRODUCTION = os.getenv('APP_ENV') == 'production'

# ==== GLOBAL DEFAULTS FROM .ENV ====
RATE_LIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '200/minute')
RATE_LIMIT_RPC = os.getenv('RATE_LIMIT_RPC', '60/minute')
RATE_LIMIT_AUTH = os.getenv('RATE_LIMIT_AUTH', '10/minute')

limiter = Limiter(key_func=get_remote_address,
                  default_limits=[RATE_LIMIT_DEFAULT])

# ==== RATE LIMITER LOGIC ====


class RPCRateLimiter:
    def __init__(self):
        self._storage = defaultdict(lambda: defaultdict(list))

    def _parse_window(self, period_str: str) -> int:
        period_str = period_str.lower().strip()
        if period_str in ['second', 'sec', 's']:
            return 1
        if period_str in ['minute', 'min', 'm']:
            return 60
        if period_str in ['hour', 'h']:
            return 3600
        if period_str in ['day', 'd']:
            return 86400

        match = re.match(r'(\d+)\s*([a-zA-Z]+)', period_str)
        if match:
            value, unit = match.groups()
            value = int(value)
            if unit.startswith('d'):
                return value * 86400
            if unit.startswith('h'):
                return value * 3600
            if unit.startswith('m'):
                return value * 60
            if unit.startswith('s'):
                return value
        return 60

    def check(self, func_key: str, ip: str, limit_str: str) -> tuple[bool, float]:
        if not limit_str:
            return True, 0.0
        try:
            parts = limit_str.split('/')
            if len(parts) != 2:
                return True, 0.0

            limit_count = int(parts[0])
            window_seconds = self._parse_window(parts[1])

            now = time.time()
            window_start = now - window_seconds

            user_history = self._storage[func_key][ip]
            valid_history = [t for t in user_history if t > window_start]

            if len(valid_history) >= limit_count:
                self._storage[func_key][ip] = valid_history
                oldest_request_time = valid_history[0]
                next_slot_time = oldest_request_time + window_seconds
                wait_time = max(1.0, next_slot_time - now)
                return False, wait_time

            valid_history.append(now)
            self._storage[func_key][ip] = valid_history
            return True, 0.0

        except Exception as e:
            print(f"[RateLimit] Error: {e}")
            return True, 0.0


rpc_limiter = RPCRateLimiter()

# ==== SERIALIZATION ====


def _serialize_result(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (list, tuple)):
        return [_serialize_result(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize_result(v) for k, v in obj.items()}
    to_dict = getattr(obj, 'to_dict', None)
    if callable(to_dict):
        return _serialize_result(to_dict())
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _serialize_result(v) for k, v in dataclasses.asdict(obj).items()}
    model_dump = getattr(obj, 'model_dump', None)
    if callable(model_dump):
        return model_dump()
    obj_dict = getattr(obj, '__dict__', None)
    if obj_dict is not None:
        return {k: _serialize_result(v) for k, v in obj_dict.items()}
    return str(obj)


def _filepath_to_route(filepath: str) -> Optional[str]:
    files_index = get_files_index()
    filepath = filepath.replace('\\', '/')

    for route_entry in files_index.routes:
        if route_entry.fs_dir:
            pattern = f'/src/app/{route_entry.fs_dir}/index.py'
            if filepath.endswith(pattern) or pattern in filepath:
                return route_entry.url_path

    if filepath.endswith('/src/app/index.py'):
        return '/'

    return None

# ==== DECORATOR ====


def rpc(require_auth: bool = False,
        allowed_roles: Optional[list[str]] = None,
        limits: Optional[Union[str, list[str]]] = None):
    """
    Decorator for RPC functions.

    Behavior:
    - If defined in a Page (index.py), it is scoped to that page's URL.
    - If defined in a Component, it is registered Globally (by function name).

    Rate Limit Hierarchy:
    1. Explicit 'limits' arg passed to decorator (e.g. "20/1h")
    2. If require_auth=True -> RATE_LIMIT_AUTH from .env
    3. Default -> RATE_LIMIT_RPC from .env
    """

    def decorator(func):
        frame = inspect.stack()[1]
        filepath = frame.filename
        route = _filepath_to_route(filepath)

        final_limits = []
        if limits:
            if isinstance(limits, str):
                final_limits = [limits]
            else:
                final_limits = limits
        else:
            if require_auth and RATE_LIMIT_AUTH:
                final_limits = [RATE_LIMIT_AUTH]
            elif RATE_LIMIT_RPC:
                final_limits = [RATE_LIMIT_RPC]

        if route is not None:
            key = f"{route}:{func.__name__}"
            rpc_route_meta = route
        else:
            key = func.__name__
            rpc_route_meta = "__GLOBAL__"

        RPC_REGISTRY[key] = func
        RPC_META[key] = {
            'require_auth': require_auth,
            'allowed_roles': allowed_roles or [],
            'limits': final_limits,
            'route': rpc_route_meta
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ==== VALIDATION HELPERS ====


def _validate_origin(request: Request) -> Optional[JSONResponse]:
    origin = request.headers.get('Origin')
    if not origin:
        return None
    if not IS_PRODUCTION:
        if origin.startswith(('http://localhost:', 'http://127.0.0.1:')):
            return None
    host_url = str(request.base_url).rstrip('/')
    if CORS_ALLOWED_ORIGINS:
        if origin not in CORS_ALLOWED_ORIGINS and origin != host_url:
            return JSONResponse({'error': 'Invalid origin'}, status_code=403)
    elif origin != host_url:
        return JSONResponse({'error': 'Invalid origin'}, status_code=403)
    return None


def _validate_csrf(request: Request, session: dict) -> Optional[JSONResponse]:
    csrf_header = request.headers.get('X-CSRF-Token')
    session_token = session.get('csrf_token')
    if not csrf_header or not session_token:
        return JSONResponse({'error': 'Missing CSRF token'}, status_code=403)
    if not hmac.compare_digest(csrf_header, session_token):
        return JSONResponse({'error': 'Invalid CSRF token'}, status_code=403)
    return None


def _validate_content_type(request: Request) -> Optional[JSONResponse]:
    content_type = request.headers.get('content-type', '')
    if not content_type.startswith(('application/json', 'multipart/form-data')):
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > 0:
            return JSONResponse({'error': 'Invalid content type'}, status_code=415)
    return None


def _get_registry_key(route: str, func_name: str) -> Optional[str]:
    route = ('/' + route.strip('/')).rstrip('/') or '/'
    key = f"{route}:{func_name}"
    if key in RPC_REGISTRY:
        return key
    if func_name in RPC_REGISTRY:
        return func_name
    return None

# ==== MAIN RPC HANDLER ====


async def _handle_rpc_request(request: Request, session: dict) -> Response:
    func_name = request.headers.get('X-PP-Function')
    if not func_name:
        return JSONResponse({'error': 'Missing function name'}, status_code=400)

    route = request.url.path.rstrip('/') or '/'
    registry_key = _get_registry_key(route, func_name)
    if not registry_key:
        return JSONResponse({'error': 'Function not found'}, status_code=404)

    if error := _validate_origin(request):
        return error
    if error := _validate_content_type(request):
        return error
    if error := _validate_csrf(request, session):
        return error

    meta = RPC_META.get(registry_key, {})

    if meta.get('require_auth') and not auth.is_authenticated():
        return JSONResponse({'error': 'Authentication required'}, status_code=401)

    allowed_roles = meta.get('allowed_roles', [])
    if allowed_roles:
        user = auth.get_payload()
        if not auth.check_role(user, allowed_roles):
            return JSONResponse({'error': 'Permission denied'}, status_code=403)

    # Rate Limits
    rpc_limits = meta.get('limits', [])
    if rpc_limits:
        client_ip = request.client.host if request.client else "unknown"
        for limit_rule in rpc_limits:
            is_allowed, wait_seconds = rpc_limiter.check(
                registry_key, client_ip, limit_rule)
            if not is_allowed:
                return JSONResponse({
                    'error': f'Rate limit exceeded. Try again in {math.ceil(wait_seconds)} seconds.'
                }, status_code=429)

    # Input Parsing
    content_type = request.headers.get('content-type', '')
    if content_type.startswith('multipart/form-data'):
        form = await request.form()
        data: dict[str, Any] = {}
        for key in form:
            value = form[key]
            if isinstance(value, str):
                try:
                    data[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    data[key] = value
            else:
                data[key] = value
    else:
        try:
            data = await request.json()
        except:
            data = {}

    # Execute
    try:
        func_to_call = RPC_REGISTRY[registry_key]
        result = func_to_call(**data)

        # Handle Async Logic
        if inspect.iscoroutine(result):
            result = await result

        # 1. Handle Explicit Response Objects (Standard or Streaming)
        if isinstance(result, Response):
            location = result.headers.get("Location")
            status = result.status_code
            if location and 300 <= status < 400:
                resp = JSONResponse({"result": None})
                resp.headers["X-PP-Redirect"] = location
                resp.headers["X-PP-Redirect-Status"] = str(status)
                return resp
            return result

        # 2. Handle Auto-Streaming (Async Generators)
        # If the user used 'yield' in an async function, it returns an AsyncGenerator.
        if inspect.isasyncgen(result) or inspect.isgenerator(result):
            return SSE(result)

        # 3. Default JSON Response
        return JSONResponse({'result': _serialize_result(result)})

    except PermissionError as e:
        return JSONResponse({'error': str(e)}, status_code=403)
    except ValueError as e:
        return JSONResponse({'error': str(e)}, status_code=400)
    except Exception as e:
        print(f"[RPC Error] {registry_key}: {e}")
        traceback.print_exc()
        return JSONResponse({'error': 'Internal server error'}, status_code=500)


async def rpc_middleware(request: Request, call_next):
    if request.headers.get('X-PP-RPC') == 'true' and request.method == 'POST':
        session = dict(request.session) if hasattr(request, 'session') else {}
        return await _handle_rpc_request(request, session)

    response = await call_next(request)
    return response


def register_rpc_routes(app: FastAPI):
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse({'error': 'Rate limit exceeded.'}, status_code=429)
