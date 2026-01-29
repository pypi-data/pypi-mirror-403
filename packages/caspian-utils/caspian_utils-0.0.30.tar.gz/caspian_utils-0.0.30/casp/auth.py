from typing import Dict, Callable, Any, Optional, Union, List
import os
import re
import secrets
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from functools import wraps
import httpx
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
import asyncio


_request_ctx: ContextVar[Optional[Request]
                         ] = ContextVar('request', default=None)


@dataclass
class AuthSettings:
    """
    App behavior configuration - set via configure_auth() in main.py.
    Secrets are always read from environment variables.
    """

    # Token settings
    default_token_validity: str = "1h"
    token_auto_refresh: bool = False

    # Role-based access
    role_identifier: str = "role"
    is_role_based: bool = False

    # Route protection
    is_all_routes_private: bool = True
    private_routes: List[str] = field(default_factory=list)
    public_routes: List[str] = field(default_factory=lambda: ["/"])
    auth_routes: List[str] = field(
        default_factory=lambda: ["/signin", "/signup"])
    role_based_routes: Dict[str, List[str]] = field(
        default_factory=dict)  # e.g. {"/admin": ["admin", "superadmin"]}

    # Redirects
    default_signin_redirect: str = "/dashboard"
    default_signout_redirect: str = "/signin"
    api_auth_prefix: str = "/api/auth"

    # Callbacks (hooks for custom logic)
    on_sign_in: Optional[Callable[[dict], None]] = None
    on_sign_out: Optional[Callable[[], None]] = None
    on_auth_failure: Optional[Callable[[Request], Response]] = None

    # Secrets (always from env)
    secret_key: str = field(default_factory=lambda: os.getenv(
        "AUTH_SECRET", "default_secret_key_change_me"))
    cookie_name: str = field(default_factory=lambda: os.getenv(
        "AUTH_COOKIE_NAME", "auth_cookie"))

    def __post_init__(self):
        self.cookie_name = re.sub(
            r"\s+", "_", self.cookie_name.strip()).lower()


# Global settings instance
_settings: AuthSettings = AuthSettings()


def configure_auth(settings: AuthSettings) -> None:
    """
    Configure auth at app startup. Call this before app starts.

    Example:
        configure_auth(AuthSettings(
            default_signin_redirect="/app",
            private_routes=["/dashboard", "/settings"],
            role_based_routes={
                "/admin": ["admin", "superadmin"],
                "/reports": ["admin", "manager", "user"],
            },
            on_sign_in=lambda user: print(f"Welcome {user.get('name')}"),
        ))
    """
    global _settings
    _settings = settings
    Auth._instance = None
    Auth.get_instance()


def get_auth_settings() -> AuthSettings:
    """Get current auth settings."""
    return _settings


@dataclass
class GoogleProvider:
    """Google OAuth provider. Reads secrets from env if not provided."""
    client_id: str = field(
        default_factory=lambda: os.getenv("GOOGLE_CLIENT_ID", ""))
    client_secret: str = field(
        default_factory=lambda: os.getenv("GOOGLE_CLIENT_SECRET", ""))
    redirect_uri: str = field(
        default_factory=lambda: os.getenv("GOOGLE_REDIRECT_URI", ""))
    max_age: str = "30d"


@dataclass
class GithubProvider:
    """GitHub OAuth provider. Reads secrets from env if not provided."""
    client_id: str = field(
        default_factory=lambda: os.getenv("GITHUB_CLIENT_ID", ""))
    client_secret: str = field(
        default_factory=lambda: os.getenv("GITHUB_CLIENT_SECRET", ""))
    max_age: str = "30d"


class Auth:
    PAYLOAD_NAME = "payload_name_8639D"
    PAYLOAD_SESSION_KEY = "payload_session_key_2183A"

    _instance: Optional["Auth"] = None
    _cookie_name: str = ""
    _providers: List[Any] = []

    def __init__(self) -> None:
        self._settings = _settings
        Auth._cookie_name = self._settings.cookie_name

    @classmethod
    def get_instance(cls) -> "Auth":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_request(cls, request: Request):
        _request_ctx.set(request)

    @classmethod
    def get_request(cls) -> Optional[Request]:
        return _request_ctx.get()

    @classmethod
    def set_providers(cls, *providers) -> None:
        """Set OAuth providers for the auth instance."""
        cls._providers = list(providers)

    @classmethod
    def get_providers(cls) -> List[Any]:
        return cls._providers

    @property
    def settings(self) -> AuthSettings:
        return self._settings

    @property
    def cookie_name(self) -> str:
        return Auth._cookie_name

    def _get_session(self) -> dict:
        request = self.get_request()
        if request and hasattr(request, 'session'):
            return request.session
        return {}

    # ====
    # ROUTE CHECKING
    # ====
    def is_public_route(self, path: str) -> bool:
        """Check if path is a public route."""
        return path in self._settings.public_routes

    def is_auth_route(self, path: str) -> bool:
        """Check if path is an auth route (signin/signup)."""
        return path in self._settings.auth_routes

    def is_private_route(self, path: str) -> bool:
        """Check if path requires authentication."""
        if self._settings.is_all_routes_private:
            return not (self.is_public_route(path) or self.is_auth_route(path))
        return path in self._settings.private_routes

    def get_required_roles(self, path: str) -> Optional[List[str]]:
        """Get required roles for a path, if any."""
        return self._settings.role_based_routes.get(path)

    # ====
    # CORE AUTH METHODS
    # ====
    def sign_in(
        self,
        data: Union[dict, str, Any],
        token_validity: Optional[str] = None,
        redirect_to: Union[bool, str] = False,
    ) -> Union[str, Response]:
        validity = token_validity or self._settings.default_token_validity
        exp_time = self._calculate_expiration(validity)

        data = self._normalize_payload(data)

        payload = {
            self.PAYLOAD_NAME: data,
            "exp": exp_time,
            "iat": datetime.now(timezone.utc).timestamp(),
        }

        session = self._get_session()
        session[self.PAYLOAD_SESSION_KEY] = payload
        session["csrf_token"] = secrets.token_hex(32)

        # Call hook if configured
        if self._settings.on_sign_in:
            self._settings.on_sign_in(data if isinstance(
                data, dict) else {"value": data})

        if redirect_to is True:
            return RedirectResponse(url=self._settings.default_signin_redirect, status_code=303)
        if isinstance(redirect_to, str) and redirect_to:
            return RedirectResponse(url=redirect_to, status_code=303)

        return "ok"

    def sign_out(self, redirect_to: Optional[str] = None) -> Optional[Response]:
        session = self._get_session()
        session.pop(self.PAYLOAD_SESSION_KEY, None)
        session.pop("csrf_token", None)
        session.clear()

        # Call hook if configured
        if self._settings.on_sign_out:
            self._settings.on_sign_out()

        target = redirect_to or self._settings.default_signout_redirect
        if target:
            return RedirectResponse(url=target, status_code=303)
        return None

    def is_authenticated(self) -> bool:
        session = self._get_session()
        payload = session.get(self.PAYLOAD_SESSION_KEY)
        if not isinstance(payload, dict):
            return False

        exp = payload.get("exp")
        if exp is not None:
            try:
                now_ts = datetime.now(timezone.utc).timestamp()
                if float(exp) < now_ts:
                    session.pop(self.PAYLOAD_SESSION_KEY, None)
                    return False
            except Exception:
                session.pop(self.PAYLOAD_SESSION_KEY, None)
                return False

        if payload.get(self.PAYLOAD_NAME) is None:
            session.pop(self.PAYLOAD_SESSION_KEY, None)
            return False

        return True

    def get_payload(self) -> Optional[Dict[str, Any]]:
        session = self._get_session()
        payload = session.get(self.PAYLOAD_SESSION_KEY)
        if not isinstance(payload, dict):
            return None

        data = payload.get(self.PAYLOAD_NAME)
        if isinstance(data, dict):
            return data
        if data is not None:
            return {"value": data}
        return None

    def check_role(self, user: Any, allowed_roles: List[str]) -> bool:
        """Check if user has one of the allowed roles."""
        if isinstance(user, dict):
            user_role = user.get(self._settings.role_identifier, "")
        else:
            user_role = str(user) if user else ""
        return user_role in allowed_roles

    # ====
    # OAUTH PROVIDERS
    # ====
    def auth_providers(self, *providers) -> Optional[Response]:
        """Handle OAuth provider signin/callback routes."""
        request = self.get_request()
        if not request:
            return None

        path_parts = request.url.path.strip("/").split("/")

        # Handle signin redirects
        if request.method == "GET" and "signin" in path_parts:
            for provider in providers:
                if isinstance(provider, GithubProvider) and "github" in path_parts:
                    url = (
                        "https://github.com/login/oauth/authorize"
                        f"?scope=user:email%20read:user&client_id={provider.client_id}"
                    )
                    return RedirectResponse(url=url)

                if isinstance(provider, GoogleProvider) and "google" in path_parts:
                    url = (
                        "https://accounts.google.com/o/oauth2/v2/auth?"
                        "scope=email%20profile&response_type=code&"
                        f"client_id={provider.client_id}&"
                        f"redirect_uri={provider.redirect_uri}"
                    )
                    return RedirectResponse(url=url)

        # Handle callbacks
        code = request.query_params.get("code")
        if request.method == "GET" and "callback" in path_parts and code:
            if "github" in path_parts:
                provider = self._find_provider(providers, GithubProvider)
                if provider:
                    return self._github_callback(provider, code)
            if "google" in path_parts:
                provider = self._find_provider(providers, GoogleProvider)
                if provider:
                    return self._google_callback(provider, code)

        return None

    def _github_callback(self, provider: GithubProvider, code: str) -> Optional[Response]:
        try:
            token_resp = httpx.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
                timeout=20,
            )
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                return None

            headers = {"Authorization": f"Bearer {access_token}",
                       "Accept": "application/json"}

            email_resp = httpx.get(
                "https://api.github.com/user/emails", headers=headers, timeout=20)
            emails = email_resp.json() if isinstance(email_resp.json(), list) else []
            primary_email = next(
                (e.get("email") for e in emails if e.get(
                    "primary") and e.get("verified")), None
            )

            user_resp = httpx.get(
                "https://api.github.com/user", headers=headers, timeout=20)
            user_info = user_resp.json() if isinstance(user_resp.json(), dict) else {}

            user_data = {
                "name": user_info.get("login"),
                "email": primary_email,
                "image": user_info.get("avatar_url"),
                "provider": "github",
                "provider_id": str(user_info.get("id")) if user_info.get("id") is not None else None,
            }

            self.sign_in(user_data, provider.max_age)
            return RedirectResponse(url=self._settings.default_signin_redirect, status_code=303)
        except Exception:
            return None

    def _google_callback(self, provider: GoogleProvider, code: str) -> Optional[Response]:
        try:
            token_resp = httpx.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": provider.redirect_uri,
                },
                timeout=20,
            )
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                return None

            user_resp = httpx.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=20,
            )
            user_info = user_resp.json() if isinstance(user_resp.json(), dict) else {}

            user_data = {
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "image": user_info.get("picture"),
                "provider": "google",
                "provider_id": str(user_info.get("id")) if user_info.get("id") is not None else None,
            }

            self.sign_in(user_data, provider.max_age)
            return RedirectResponse(url=self._settings.default_signin_redirect, status_code=303)
        except Exception:
            return None

    # ====
    # HELPERS
    # ====
    def _normalize_payload(self, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        if "role" not in data:
            ur = data.get("userRole")
            if isinstance(ur, dict):
                data["role"] = (
                    ur.get("name") or ur.get("slug") or ur.get(
                        "role") or ur.get("value") or ur.get("id")
                )
            elif isinstance(ur, str):
                data["role"] = ur

        return data

    def _calculate_expiration(self, duration: str) -> int:
        match = re.match(r"^(\d+)(s|m|h|d)$", duration)
        if not match:
            raise ValueError(f"Invalid duration format: {duration}")

        value, unit = int(match.group(1)), match.group(2)
        delta = {
            "s": timedelta(seconds=value),
            "m": timedelta(minutes=value),
            "h": timedelta(hours=value),
            "d": timedelta(days=value),
        }[unit]

        return int((datetime.now(timezone.utc) + delta).timestamp())

    def _find_provider(self, providers, provider_type):
        for p in providers:
            if isinstance(p, provider_type):
                return p
        return None


# Singleton instance
auth = Auth.get_instance()


# ====
# BACKWARDS COMPATIBILITY
# ====
class AuthConfig:
    """Backwards compatibility alias."""
    PUBLIC_ROUTES = property(lambda self: _settings.public_routes)
    PRIVATE_ROUTES = property(lambda self: _settings.private_routes)
    AUTH_ROUTES = property(lambda self: _settings.auth_routes)
    IS_ALL_ROUTES_PRIVATE = property(
        lambda self: _settings.is_all_routes_private)
    DEFAULT_SIGNIN_REDIRECT = property(
        lambda self: _settings.default_signin_redirect)
    DEFAULT_SIGNOUT_REDIRECT = property(
        lambda self: _settings.default_signout_redirect)

    @staticmethod
    def check_auth_role(user: Any, allowed_roles: List[str]) -> bool:
        return auth.check_role(user, allowed_roles)


# ====
# DECORATORS
# ====
def require_auth(redirect_to: Optional[str] = None):
    """Decorator to require authentication for a route."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = Auth.get_request()
            if not auth.is_authenticated():
                if auth.settings.on_auth_failure and request:
                    return auth.settings.on_auth_failure(request)
                target = redirect_to or "/signin"
                next_url = request.url.path if request else "/"
                return RedirectResponse(url=f"{target}?next={next_url}", status_code=303)
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles: str, redirect_to: str = "/unauthorized"):
    """Decorator to require specific roles for a route. Roles are strings."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = Auth.get_request()
            if not auth.is_authenticated():
                path = request.url.path if request else "/"
                return RedirectResponse(url=f"/signin?next={path}", status_code=303)

            user = auth.get_payload()
            if not auth.check_role(user, list(roles)):
                return RedirectResponse(url=redirect_to, status_code=303)

            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator


def guest_only(redirect_to: Optional[str] = None):
    """Decorator for routes that should only be accessible to non-authenticated users."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = Auth.get_request()
            if auth.is_authenticated():
                target = redirect_to or auth.settings.default_signin_redirect
                next_url = request.query_params.get(
                    "next", target) if request else target
                return RedirectResponse(url=next_url, status_code=303)
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator


def get_csrf_token() -> str:
    """Get or generate CSRF token from session."""
    request = Auth.get_request()
    if request and hasattr(request, 'session'):
        csrf_token = request.session.get("csrf_token")
        if not csrf_token:
            csrf_token = secrets.token_hex(32)
            request.session["csrf_token"] = csrf_token
        return csrf_token
    return ""
