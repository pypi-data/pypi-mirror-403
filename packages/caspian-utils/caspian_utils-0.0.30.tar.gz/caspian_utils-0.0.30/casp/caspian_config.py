from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple
import json
import os

# ====
# Path & Root Logic (Fixed for PyPI Package)
# ====


def _get_project_root() -> Path:
    """
    Determine the project root.
    1. Checks CASPIAN_ROOT env var (allows explicit override).
    2. Falls back to Path.cwd() (the user's current working directory).
    """
    env_root = os.getenv("CASPIAN_ROOT")
    if env_root:
        return Path(env_root).resolve()

    # This ensures we look in the folder where the user runs the command,
    # rather than inside the installed site-packages folder.
    return Path.cwd().resolve()


PROJECT_ROOT = _get_project_root()

# Define default paths relative to the user's project root
DEFAULT_CONFIG_PATH = (PROJECT_ROOT / "caspian.config.json").resolve()
DEFAULT_FILES_LIST_PATH = (
    PROJECT_ROOT / "settings" / "files-list.json").resolve()


# ====
# Errors
# ====

class CaspianConfigError(ValueError):
    """Raised when caspian.config.json is missing fields or has invalid types."""


class FilesListError(ValueError):
    """Raised when settings/files-list.json is invalid or cannot be categorized."""


# ====
# Small validators
# ====

def _require(data: Mapping[str, Any], key: str) -> Any:
    if key not in data:
        raise CaspianConfigError(f"Missing required key: {key}")
    return data[key]


def _expect_str(value: Any, key: str) -> str:
    if not isinstance(value, str):
        raise CaspianConfigError(
            f"Expected '{key}' to be str, got {type(value).__name__}")
    return value


def _expect_bool(value: Any, key: str) -> bool:
    if not isinstance(value, bool):
        raise CaspianConfigError(
            f"Expected '{key}' to be bool, got {type(value).__name__}")
    return value


def _expect_str_list(value: Any, key: str) -> List[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise CaspianConfigError(f"Expected '{key}' to be List[str]")
    return value


def _expect_str_dict(value: Any, key: str) -> Dict[str, str]:
    if not isinstance(value, dict):
        raise CaspianConfigError(
            f"Expected '{key}' to be Dict[str, str], got {type(value).__name__}")
    for k, v in value.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise CaspianConfigError(
                f"Expected '{key}' to be Dict[str, str] (found non-str key/value)")
    return dict(value)


# ====
# caspian.config.json (type-safe)
# ====

@dataclass(frozen=True, slots=True)
class CaspianConfig:
    projectName: str
    projectRootPath: Path
    bsTarget: str
    bsPathRewrite: Dict[str, str]

    backendOnly: bool
    tailwindcss: bool
    mcp: bool
    prisma: bool
    typescript: bool

    version: str
    componentScanDirs: List[str]
    excludeFiles: List[str]

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "CaspianConfig":
        projectName = _expect_str(_require(data, "projectName"), "projectName")
        projectRootPath_raw = _expect_str(
            _require(data, "projectRootPath"), "projectRootPath")
        bsTarget = _expect_str(_require(data, "bsTarget"), "bsTarget")
        bsPathRewrite = _expect_str_dict(
            _require(data, "bsPathRewrite"), "bsPathRewrite")

        backendOnly = _expect_bool(
            _require(data, "backendOnly"), "backendOnly")
        tailwindcss = _expect_bool(
            _require(data, "tailwindcss"), "tailwindcss")
        mcp = _expect_bool(_require(data, "mcp"), "mcp")
        prisma = _expect_bool(_require(data, "prisma"), "prisma")
        typescript = _expect_bool(_require(data, "typescript"), "typescript")

        version = _expect_str(_require(data, "version"), "version")
        componentScanDirs = _expect_str_list(
            _require(data, "componentScanDirs"), "componentScanDirs")
        excludeFiles = _expect_str_list(
            _require(data, "excludeFiles"), "excludeFiles")

        return CaspianConfig(
            projectName=projectName,
            projectRootPath=Path(projectRootPath_raw),
            bsTarget=bsTarget,
            bsPathRewrite=bsPathRewrite,
            backendOnly=backendOnly,
            tailwindcss=tailwindcss,
            mcp=mcp,
            prisma=prisma,
            typescript=typescript,
            version=version,
            componentScanDirs=componentScanDirs,
            excludeFiles=excludeFiles,
        )

    @staticmethod
    def from_json(text: str) -> "CaspianConfig":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise CaspianConfigError(f"Invalid JSON: {e}") from e
        if not isinstance(data, dict):
            raise CaspianConfigError("Top-level JSON must be an object")
        return CaspianConfig.from_dict(data)

    @staticmethod
    def from_file(path: str | Path) -> "CaspianConfig":
        p = Path(path)
        if not p.exists():
            raise CaspianConfigError(f"Config file not found: {p}")
        return CaspianConfig.from_json(p.read_text(encoding="utf-8"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projectName": self.projectName,
            "projectRootPath": str(self.projectRootPath),
            "bsTarget": self.bsTarget,
            "bsPathRewrite": dict(self.bsPathRewrite),
            "backendOnly": self.backendOnly,
            "tailwindcss": self.tailwindcss,
            "mcp": self.mcp,
            "prisma": self.prisma,
            "typescript": self.typescript,
            "version": self.version,
            "componentScanDirs": list(self.componentScanDirs),
            "excludeFiles": list(self.excludeFiles),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: str | Path, *, indent: int = 2) -> None:
        Path(path).write_text(self.to_json(indent=indent), encoding="utf-8")


def load_config(path: str | Path | None = None) -> CaspianConfig:
    """
    Load and validate ./caspian.config.json.
    Defaults to the file in the current working directory if no path is provided.
    """
    if path is None:
        path = DEFAULT_CONFIG_PATH
    return CaspianConfig.from_file(path)


# ====
# settings/files-list.json (type-safe + categorized)
# ====

APP_ROOT_PREFIX = "./src/app/"


@dataclass(frozen=True, slots=True)
class RouteEntry:
    """
    Derived from ./src/app/**/index.(py|html)
    - fs_dir: filesystem-relative dir inside src/app (keeps groups like (auth))
    - url_path: URL path (removes groups like (auth))
    - fastapi_rule: URL path converted to a FastAPI-friendly rule ({id}, {tags:path})
    - has_py/has_html: whether index.py / index.html exists for that route
    """
    fs_dir: str
    url_path: str
    fastapi_rule: str
    has_py: bool
    has_html: bool


@dataclass(frozen=True, slots=True)
class LayoutEntry:
    """Derived from ./src/app/**/layout.html"""
    fs_dir: str
    url_scope: str
    file: str


@dataclass(frozen=True, slots=True)
class LoadingEntry:
    """Derived from ./src/app/**/loading.html"""
    fs_dir: str
    url_scope: str
    file: str


@dataclass(frozen=True, slots=True)
class FilesIndex:
    """
    Categorization rules:
      - routing: only index.py + index.html under ./src/app
      - layout: layout.html under ./src/app
      - loadings: loading.html under ./src/app
      - general_app: everything else under ./src/app
      - general_other: everything outside ./src/app
    """
    routes: List[RouteEntry]
    layouts: List[LayoutEntry]
    loadings: List[LoadingEntry]
    general_app: List[str]
    general_other: List[str]


def _is_ignored_build_artifact(p: str) -> bool:
    return "/__pycache__/" in p or p.endswith(".pyc")


def _strip_app_prefix(p: str) -> Optional[str]:
    if p.startswith(APP_ROOT_PREFIX):
        return p[len(APP_ROOT_PREFIX):]
    return None


def _split_dir_and_file(app_rel: str) -> Tuple[str, str]:
    parts = app_rel.split("/")
    if len(parts) == 1:
        return "", parts[0]
    return "/".join(parts[:-1]), parts[-1]


def _is_group_segment(seg: str) -> bool:
    return seg.startswith("(") and seg.endswith(")")


def _to_url_path(fs_dir: str) -> str:
    if not fs_dir:
        return "/"
    segs = [s for s in fs_dir.split("/") if s and not _is_group_segment(s)]
    return "/" + "/".join(segs) if segs else "/"


def _to_fastapi_rule(url_path: str) -> str:
    """Convert URL path to FastAPI format: [id] -> {id}, [...tags] -> {tags:path}"""
    if url_path == "/":
        return "/"
    out: List[str] = []
    for seg in url_path.strip("/").split("/"):
        if seg.startswith("[...") and seg.endswith("]") and len(seg) > 5:
            name = seg[4:-1].strip() or "path"
            out.append(f"{{{name}:path}}")
        elif seg.startswith("[") and seg.endswith("]") and len(seg) > 2:
            name = seg[1:-1].strip() or "param"
            out.append(f"{{{name}}}")
        else:
            out.append(seg)
    return "/" + "/".join(out)


def load_files_list(path: str | Path | None = None) -> List[str]:
    """Load settings/files-list.json (expects a JSON array of strings)."""
    if path is None:
        path = DEFAULT_FILES_LIST_PATH

    p = Path(path)
    if not p.exists():
        raise FilesListError(f"Files list not found: {p}")

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise FilesListError(f"Invalid JSON in files-list.json: {e}") from e

    if not isinstance(raw, list) or any(not isinstance(x, str) for x in raw):
        raise FilesListError("files-list.json must be a JSON array of strings")

    return raw


def build_files_index(file_paths: List[str]) -> FilesIndex:
    routes_map: Dict[str, Dict[str, bool]] = {}
    layouts: List[LayoutEntry] = []
    loadings: List[LoadingEntry] = []
    general_app: List[str] = []
    general_other: List[str] = []

    for p in file_paths:
        if _is_ignored_build_artifact(p):
            continue

        app_rel = _strip_app_prefix(p)
        if app_rel is None:
            general_other.append(p)
            continue

        fs_dir, filename = _split_dir_and_file(app_rel)

        if filename == "index.py" or filename == "index.html":
            bucket = routes_map.setdefault(
                fs_dir, {"py": False, "html": False})
            if filename == "index.py":
                bucket["py"] = True
            else:
                bucket["html"] = True
            continue

        if filename == "layout.html":
            url_scope = _to_url_path(fs_dir)
            layouts.append(LayoutEntry(
                fs_dir=fs_dir, url_scope=url_scope, file=p))
            continue

        if filename == "loading.html":
            url_scope = _to_url_path(fs_dir)
            loadings.append(LoadingEntry(
                fs_dir=fs_dir, url_scope=url_scope, file=p))
            continue

        general_app.append(p)

    routes: List[RouteEntry] = []
    for fs_dir, flags in routes_map.items():
        url_path = _to_url_path(fs_dir)
        routes.append(
            RouteEntry(
                fs_dir=fs_dir,
                url_path=url_path,
                fastapi_rule=_to_fastapi_rule(url_path),
                has_py=bool(flags.get("py")),
                has_html=bool(flags.get("html")),
            )
        )

    def route_sort_key(r: RouteEntry):
        is_dynamic = "{" in r.fastapi_rule
        is_catch_all = ":path}" in r.fastapi_rule

        priority = 0
        if is_catch_all:
            priority = 2
        elif is_dynamic:
            priority = 1

        return (priority, r.fs_dir)

    routes.sort(key=route_sort_key)

    layouts.sort(key=lambda x: x.fs_dir)
    loadings.sort(key=lambda x: x.fs_dir)
    general_app.sort()
    general_other.sort()

    return FilesIndex(
        routes=routes,
        layouts=layouts,
        loadings=loadings,
        general_app=general_app,
        general_other=general_other,
    )


def load_files_index(path: str | Path | None = None) -> FilesIndex:
    """Convenience: load + categorize ./settings/files-list.json."""
    return build_files_index(load_files_list(path))


_cached_config: CaspianConfig | None = None
_cached_files_index: FilesIndex | None = None


def get_config() -> CaspianConfig:
    """Cached single source of truth for caspian.config.json"""
    global _cached_config
    if _cached_config is None:
        _cached_config = load_config()
    return _cached_config


def get_files_index() -> FilesIndex:
    """Cached single source of truth for files-list.json"""
    global _cached_files_index
    if _cached_files_index is None:
        _cached_files_index = load_files_index()
    return _cached_files_index


if __name__ == "__main__":
    try:
        cfg = load_config()
        idx = load_files_index()

        print("Project:", cfg.projectName)
        print("Config root:", cfg.projectRootPath)

        print("\nRoutes (Sorted Priority):")
        for r in idx.routes:
            print(
                f" - fs_dir='{r.fs_dir or '.'}' url='{r.url_path}' fastapi='{r.fastapi_rule}' "
                f"(py={r.has_py}, html={r.has_html})"
            )

        print("\nLayouts:")
        for l in idx.layouts:
            print(
                f" - scope='{l.url_scope}' fs_dir='{l.fs_dir or '.'}' file='{l.file}'")

        print("\nLoadings:")
        for l in idx.loadings:
            print(
                f" - scope='{l.url_scope}' fs_dir='{l.fs_dir or '.'}' file='{l.file}'")

        print(f"\nGeneral (src/app): {len(idx.general_app)} files")
        print(f"General (outside src/app): {len(idx.general_other)} files")

    except Exception as e:
        print(f"Error running configuration test: {e}")
