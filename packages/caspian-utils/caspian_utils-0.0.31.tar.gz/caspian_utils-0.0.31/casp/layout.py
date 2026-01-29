from __future__ import annotations
from typing import Literal
from typing import Callable
import os
import json
import hashlib
import importlib.util
import inspect
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from jinja2 import Environment, BaseLoader, select_autoescape
from markupsafe import Markup
import contextvars

_runtime_metadata: contextvars.ContextVar[Optional["Metadata"]] = contextvars.ContextVar("casp_metadata", default=None)
_runtime_injections: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar("casp_injections", default=None)

class LayoutEngine:
    """
    Single source of truth for:
      - Jinja environment (Caspian delimiters)
      - Template loading (file + relative-to-py)
      - Rendering (string + page + layout)
      - Nested layout system (Next.js style layout discovery and wrapping)

    Canonical public entrypoints:
      - render_page(__file__, context)   -> index.html
      - render_layout(__file__, context) -> layout.html

    No load_page/load_layout helpers exist in this module by design.
    """

    def __init__(self) -> None:
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(["html", "xml"]),
            variable_start_string="[[",
            variable_end_string="]]",
            block_start_string="[%",  # Caspian blocks
            block_end_string="%]",
        )
        self.env.filters["json"] = self._to_safe_json
        self.env.filters["dump"] = self._to_safe_json

        # Legacy alias used elsewhere
        self.string_env = self.env

    # ---------------------------------------------------------------------
    # Jinja helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _to_safe_json(value: Any) -> Markup:
        """Safely serialize to JSON for HTML/JS embedding."""
        s = json.dumps(value, ensure_ascii=False, default=str)
        escaped = (
            s.replace("</", "<\\/")
            .replace("<!--", "<\\!--")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )
        return Markup(escaped)

    # ---------------------------------------------------------------------
    # Core template loading & rendering
    # ---------------------------------------------------------------------

    def load_template_file(self, file_path: str) -> str:
        """Load template file directly by absolute/relative path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Template not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def load_template(self, py_file: str, template_name: Optional[str] = None) -> str:
        """
        Load HTML template relative to a Python file.

        Args:
            py_file: Pass __file__ from calling module
            template_name: Template filename (auto-detected if None -> sibling .html)
        """
        dir_path = os.path.dirname(os.path.abspath(py_file))
        if template_name is None:
            template_name = os.path.basename(py_file).replace(".py", ".html")
        html_path = os.path.join(dir_path, template_name)
        return self.load_template_file(html_path)

    def render(
        self,
        py_file: str,
        context: Optional[Dict[str, Any]] = None,
        template_name: Optional[str] = None,
    ) -> str:
        """
        Unified render function with Caspian Syntax support.
        Handles: <[[ component ]]> | <template casp-for> | <template casp-if>
        """
        # LOCAL IMPORTS to prevent circular dependency
        from casp.syntax_compiler import transpile_syntax
        from casp.components_compiler import process_imports

        ctx = context.copy() if context else {}
        template_str = self.load_template(py_file, template_name)
        
        # 1. Transpile Syntax (Convert Caspian Syntax -> Jinja)
        template_str = transpile_syntax(template_str)
        
        # 2. Extract Imports (Get mapping of "House" -> ComponentClass)
        base_dir = os.path.dirname(os.path.abspath(py_file))
        _, alias_map = process_imports(template_str, base_dir=base_dir)
        
        # 3. Define Dynamic Renderer Helper
        def render_dynamic(target, props=None, caller=None):
            props = props or {}
            
            # Resolve String Alias (e.g. "House") using local map
            comp = target
            if isinstance(target, str) and target in alias_map:
                comp = alias_map[target]
            
            # Render Component
            if callable(comp):
                if caller: props['children'] = caller()
                return comp(**props)
            
            # Fallback: Display Data
            return str(target) if target is not None else ""

        # Inject helper into context so Jinja can call it
        ctx['render_dynamic'] = render_dynamic
        
        template = self.env.from_string(template_str)
        return template.render(**ctx)

    def render_page(self, py_file: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Render index.html with context."""
        return self.render(py_file, context, "index.html")

    def render_layout(self, py_file: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Render layout.html with context.

        If context is None, returns the raw layout.html string (no Jinja render).
        """
        if context is None:
            return self.load_template(py_file, "layout.html")

        # Preserve [[ children ]] tag if caller didn't provide children
        if "children" not in context:
            context["children"] = Markup("[[ children ]]")

        return self.render(py_file, context, "layout.html")

    # ---------------------------------------------------------------------
    # Layout system (Next.js style layout discovery and wrapping)
    # ---------------------------------------------------------------------

    @dataclass
    class LayoutInfo:
        dir_path: str
        has_py: bool
        has_html: bool

        @property
        def layout_id(self) -> str:
            return hashlib.md5(self.dir_path.encode()).hexdigest()[:8]

        @property
        def py_path(self) -> str:
            return os.path.join(self.dir_path, "layout.py")

        @property
        def html_path(self) -> str:
            return os.path.join(self.dir_path, "layout.html")

    @dataclass
    class LayoutResult:
        content: str
        # Props from the tuple return (Visual Data -> [[layout.*]])
        props: Dict[str, Any] = field(default_factory=dict)
        # Metadata from the Metadata class (SEO Data -> [[metadata.*]])
        meta: Dict[str, Any] = field(default_factory=dict)

    def discover_layouts(self, route_dir: str) -> List["LayoutEngine.LayoutInfo"]:
        """Find all layouts from root to route (Next.js style)."""
        route_dir = route_dir.replace("\\", "/")
        rel_path = os.path.relpath(route_dir, "src/app").replace("\\", "/")

        layouts: List[LayoutEngine.LayoutInfo] = []

        def check_dir(dir_path: str) -> Optional[LayoutEngine.LayoutInfo]:
            dir_path = dir_path.replace("\\", "/")
            html_exists = os.path.exists(os.path.join(dir_path, "layout.html"))
            py_exists = os.path.exists(os.path.join(dir_path, "layout.py"))
            if html_exists or py_exists:
                return LayoutEngine.LayoutInfo(
                    dir_path=dir_path,
                    has_py=py_exists,
                    has_html=html_exists,
                )
            return None

        root = check_dir("src/app")
        if root:
            layouts.append(root)

        current = "src/app"
        for segment in rel_path.split("/"):
            if segment in (".", "src", "app", ""):
                continue
            current = os.path.join(current, segment).replace("\\", "/")
            found = check_dir(current)
            if found:
                layouts.append(found)

        return layouts

    def load_layout_module(self, py_path: str):
        """Dynamically load layout.py module."""
        if not os.path.exists(py_path):
            return None

        module_name = f"layout_{hashlib.md5(py_path.encode()).hexdigest()}"
        spec = importlib.util.spec_from_file_location(module_name, py_path)
        if not (spec and spec.loader):
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def resolve_layout(
        self,
        layout: "LayoutEngine.LayoutInfo",
        context: Dict[str, Any],
    ) -> "LayoutEngine.LayoutResult":
        """
        Resolve layout content with Namespace Separation.
        - Tuple Return -> populates [[layout.*]] (Visuals)
        - Metadata Class -> populates [[metadata.*]] (SEO)
        """
        passthrough = "[[ children | safe ]]"

        if layout.has_py:
            module = self.load_layout_module(layout.py_path)

            if module and not hasattr(module, "layout"):
                raise AttributeError(
                    f"The file '{layout.py_path}' is missing the required 'def layout():' function."
                )

            if module:
                # 1. Reset Metadata Context
                _runtime_metadata.set(None)

                # 2. Execute Layout Function
                sig = inspect.signature(module.layout)
                result = module.layout(
                    context) if sig.parameters else module.layout()

                # 3. Capture SEO Metadata ([[metadata.*]])
                # Priority: Dynamic > Static
                dynamic_meta_obj = _runtime_metadata.get()
                static_meta_obj = getattr(module, 'metadata', None)
                
                meta_dict = {}
                
                def extract_meta(obj):
                    if not obj: return {}
                    d = {}
                    if obj.title: d['title'] = obj.title
                    if obj.description: d['description'] = obj.description
                    if obj.extra: d.update(obj.extra)
                    return d

                # Apply Static then Dynamic (Dynamic overrides)
                meta_dict.update(extract_meta(static_meta_obj))
                meta_dict.update(extract_meta(dynamic_meta_obj))

                # 4. Capture Layout Props ([[layout.*]])
                content = passthrough
                props_dict = {}

                if result is None:
                    if layout.has_html:
                        content = self.load_template_file(layout.html_path)
                elif isinstance(result, str):
                    content = result
                elif isinstance(result, tuple) and len(result) == 2:
                    content = result[0]
                    props_dict = result[1] or {}
                elif isinstance(result, dict):
                    if layout.has_html:
                        content = self.load_template_file(layout.html_path)
                    props_dict = result

                # 5. STRICT FILTERING
                # Remove SEO keys from Visual Props to prevent confusion
                if 'title' in props_dict:
                    del props_dict['title']
                if 'description' in props_dict:
                    del props_dict['description']

                return LayoutEngine.LayoutResult(content, props_dict, meta_dict)

        if layout.has_html:
            return LayoutEngine.LayoutResult(self.load_template_file(layout.html_path))

        return LayoutEngine.LayoutResult(passthrough)

    def get_loading_files(self) -> str:
        """Get loading indicator HTML."""
        try:
            from .loading import get_loading_files as _get_loading
            return _get_loading()
        except ImportError:
            return ""

    def _inject_meta(self, html: str, layout_id: str) -> str:
        """Inject root layout meta tag."""
        meta = f'<meta name="pp-root-layout" content="{layout_id}">'
        if "<head>" in html:
            return html.replace("<head>", f"<head>\n    {meta}")
        return html

    def render_with_nested_layouts(
        self,
        children: str,
        route_dir: str,
        page_metadata: Optional[Dict[str, Any]] = None,
        page_layout_props: Optional[Dict[str, Any]] = None,
        context_data: Optional[Dict[str, Any]] = None,
        transform_fn=None,
        component_compiler: Optional[Callable] = None,
    ) -> Tuple[str, str]:
        """
        Render page wrapped in nested layouts with strict namespace merging.
        Integrates syntax transpilation (<[[...]]>) and dynamic component resolution.
        """
        # LOCAL IMPORTS to prevent circular dependency
        from casp.syntax_compiler import transpile_syntax
        from casp.components_compiler import process_imports

        context = context_data or {}

        layouts = self.discover_layouts(route_dir)
        root_id = layouts[0].layout_id if layouts else "default"

        # === DYNAMIC RENDERER HELPER (Shared Logic) ===
        def render_dynamic_helper(target, props=None, caller=None, alias_map=None):
            props = props or {}
            alias_map = alias_map or {}
            
            comp = target
            if isinstance(target, str) and target in alias_map:
                comp = alias_map[target]
            
            if callable(comp):
                if caller: props['children'] = caller()
                return comp(**props)
            return str(target) if target is not None else ""

        # --- CASE 1: No Layouts (Direct Page Render - usually raw HTML file) ---
        if not layouts:
            # 1. Transpile
            html = transpile_syntax(children)
            # 2. Imports
            _, alias_map = process_imports(html, base_dir=route_dir)
            # 3. Context Helper
            context['render_dynamic'] = lambda t, p=None, c=None: render_dynamic_helper(t, p, c, alias_map)
            
            template = self.env.from_string(html)
            html = template.render(**context)
            
            html += self.get_loading_files()
            if transform_fn:
                html = transform_fn(html)
            return html, root_id

        # --- CASE 2: Nested Layouts ---
        current_html = children
        
        accumulated_meta = {}
        accumulated_props = {}
        resolved_layers = []

        # 1. Resolve Data
        for layout in layouts:
            res = self.resolve_layout(layout, context)
            resolved_layers.append(res)
            accumulated_meta.update(res.meta)
            accumulated_props.update(res.props)

        if page_metadata: accumulated_meta.update(page_metadata)
        if page_layout_props: accumulated_props.update(page_layout_props)

        # 2. Render Layers
        for i, layout in enumerate(reversed(layouts)):
            is_root = i == (len(layouts) - 1)
            layer_result = resolved_layers[len(layouts) - 1 - i]
            layer_content = layer_result.content

            # A. TRANSPILE (for raw HTML layouts)
            layer_content = transpile_syntax(layer_content)

            # B. EXTRACT IMPORTS (for this layout layer)
            _, alias_map = process_imports(layer_content, base_dir=layout.dir_path)
            
            # C. CONTEXT SETUP
            layer_context = context.copy()
            layer_context['render_dynamic'] = lambda t, p=None, c=None: render_dynamic_helper(t, p, c, alias_map)

            if is_root:
                current_html += self.get_loading_files()
                layer_content = self._inject_meta(layer_content, root_id)

            template = self.env.from_string(layer_content)
            current_html = template.render(
                children=Markup(current_html),
                layout=accumulated_props,
                metadata=accumulated_meta,
                **layer_context,
            )

            if component_compiler:
                current_html = component_compiler(current_html, base_dir=layout.dir_path)

        injections = _runtime_injections.get()
        if injections:
            if injections.get('head'):
                head_block = "\n".join(injections['head'])
                # Regex replace might be safer, but simple string replace is faster 
                # and covers 99% of valid HTML cases
                current_html = current_html.replace("</head>", f"{head_block}\n</head>")
            
            if injections.get('body'):
                body_block = "\n".join(injections['body'])
                current_html = current_html.replace("</body>", f"{body_block}\n</body>")

        if transform_fn:
            current_html = transform_fn(current_html)

        return current_html, root_id

@dataclass
class Metadata:
    title: Optional[str] = None
    description: Optional[str] = None
    extra: Optional[Dict[str, str]] = None 

    def __post_init__(self):
        # Initialize dictionary if None
        if self.extra is None:
            self.extra = {}
            
        # 1. Dynamic Usage: Set context var (for usage inside functions)
        _runtime_metadata.set(self)
        
        # 2. Static Usage: Auto-register to module globals
        # This fixes the issue where unassigned Metadata(...) was ignored.
        try:
            # Stack: __post_init__ (0) -> __init__ (1) -> Caller (2)
            frame = inspect.currentframe()
            if frame and frame.f_back and frame.f_back.f_back:
                caller_frame = frame.f_back.f_back
                
                # Only auto-register if called at module level
                if caller_frame.f_code.co_name == '<module>':
                    # Magically set 'metadata' variable in that file
                    caller_frame.f_globals['metadata'] = self
        except Exception:
            pass


# -----------------------------------------------------------------------------
# Singleton + module-level API (single source of truth)
# -----------------------------------------------------------------------------

_engine = LayoutEngine()

# Jinja env exports
env = _engine.env
string_env = _engine.string_env

# Core exports


def load_template_file(file_path: str) -> str:
    return _engine.load_template_file(file_path)


def load_template(py_file: str, template_name: Optional[str] = None) -> str:
    return _engine.load_template(py_file, template_name)


def render(
    py_file: str,
    context: Optional[Dict[str, Any]] = None,
    template_name: Optional[str] = None,
) -> str:
    return _engine.render(py_file, context, template_name)


def render_page(py_file: str, context: Optional[Dict[str, Any]] = None) -> str:
    return _engine.render_page(py_file, context)


def render_layout(py_file: str, context: Optional[Dict[str, Any]] = None) -> str:
    return _engine.render_layout(py_file, context)


# Layout system exports
LayoutInfo = LayoutEngine.LayoutInfo
LayoutResult = LayoutEngine.LayoutResult


def discover_layouts(route_dir: str) -> List[LayoutInfo]:
    return _engine.discover_layouts(route_dir)


def load_layout_module(py_path: str):
    return _engine.load_layout_module(py_path)


def resolve_layout(layout: LayoutInfo, context: Dict[str, Any]) -> LayoutResult:
    return _engine.resolve_layout(layout, context)


def get_loading_files() -> str:
    return _engine.get_loading_files()


def render_with_nested_layouts(
    children: str,
    route_dir: str,
    page_metadata: Optional[Dict[str, Any]] = None,
    page_layout_props: Optional[Dict[str, Any]] = None,
    context_data: Optional[Dict[str, Any]] = None,
    transform_fn=None,
    component_compiler: Optional[Callable] = None,
) -> Tuple[str, str]:
    return _engine.render_with_nested_layouts(
        children=children,
        route_dir=route_dir,
        page_metadata=page_metadata,
        page_layout_props=page_layout_props,
        context_data=context_data,
        transform_fn=transform_fn,
        component_compiler=component_compiler,
    )

def inject_html(file_path: str, target: Literal['head', 'body'] = 'head', **kwargs) -> None:
    """
    Inject HTML content from a file into the <head> or <body> of the final render.
    
    Args:
        file_path: Path to the HTML file (relative to the calling python file).
        target: Where to inject ('head' or 'body').
        **kwargs: Variables to replace in the file using [[ var ]] syntax.
    """
    # 1. Resolve path relative to caller
    frame = inspect.currentframe()
    base_dir = None
    if frame and frame.f_back:
        # Go back to the caller frame
        caller_file = frame.f_back.f_globals.get('__file__')
        if caller_file:
            base_dir = os.path.dirname(os.path.abspath(caller_file))
    
    if base_dir and not os.path.isabs(file_path):
        full_path = os.path.join(base_dir, file_path)
    else:
        full_path = file_path

    # 2. Load and Render with Caspian String Env
    try:
        if os.path.exists(full_path):
            content = load_template_file(full_path)
            # Use string_env to support [[ content_id ]] params
            rendered_content = string_env.from_string(content).render(**kwargs)
            
            # 3. Store in Context
            store = _runtime_injections.get()
            if store is not None:
                tgt = target.lower()
                if tgt in store:
                    store[tgt].append(rendered_content)
        else:
            print(f"[Caspian] Warning: inject_html file not found: {full_path}")
    except Exception as e:
        print(f"[Caspian] Error injecting html from {file_path}: {e}")

# Back-compat alias (if referenced elsewhere)
render_with_layouts = render_with_nested_layouts


__all__ = [
    "LayoutEngine",
    "env",
    "string_env",
    "load_template_file",
    "load_template",
    "render",
    "render_page",
    "render_layout",
    "LayoutInfo",
    "LayoutResult",
    "discover_layouts",
    "resolve_layout",
    "load_layout_module",
    "get_loading_files",
    "render_with_nested_layouts",
    "render_with_layouts",
    "inject_html",
    "_runtime_injections",
]