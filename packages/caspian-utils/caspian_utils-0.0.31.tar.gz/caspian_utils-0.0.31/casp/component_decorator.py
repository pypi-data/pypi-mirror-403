from .layout import env, load_template_file
from .html_attrs import get_attributes, merge_classes
from .syntax_compiler import transpile_syntax
from .caspian_config import get_config
from typing import Callable, TypeVar, Dict, Optional, Any, Union
from markupsafe import Markup
import inspect
import os
import importlib
import importlib.util

R = TypeVar('R')

_component_registry: Dict[str, 'Component'] = {}


class Component:
    """Wrapper class for PulsePoint components"""
    _is_pp_component: bool = True
    source_path: Optional[str] = None

    def __init__(self, fn: Callable[..., str], source_path: Optional[str] = None):
        self.fn = fn
        self.source_path = source_path
        self.__name__ = fn.__name__
        self.__doc__ = fn.__doc__
        self.__signature__ = inspect.signature(fn)
        _component_registry[fn.__name__] = self

    def __call__(self, *args, **kwargs) -> Union[str, Markup]:
        # 1. Gather all class variants
        c_raw = kwargs.get("class")
        c_name = kwargs.get("class_name")
        c_react = kwargs.pop("className", None)  # Remove React-style key

        # 2. Filter valid inputs
        candidates = []
        for c in [c_raw, c_name, c_react]:
            if c:
                candidates.append(c)

        # 3. Merge if any exist
        if candidates:
            try:
                # Check config to decide strategy
                cfg = get_config()
                use_tailwind = cfg.tailwindcss
            except Exception:
                # Fallback safety if config isn't loaded
                use_tailwind = False

            if use_tailwind:
                # Strategy A: Smart Merge (Tailwind)
                merged = merge_classes(*candidates)
            else:
                # Strategy B: Simple Join (Vanilla CSS)
                parts = []
                for c in candidates:
                    if isinstance(c, (list, tuple, set)):
                        parts.append(" ".join(str(x) for x in c if x))
                    else:
                        parts.append(str(c).strip())
                merged = " ".join(p for p in parts if p)

            # A. Always set 'class' (The Standard)
            # This ensures props['class'] is available for get_attributes()
            kwargs["class"] = merged

            # B. Only set 'class_name' if explicitly requested
            # This prevents duplication in **props
            if "class_name" in self.__signature__.parameters:
                kwargs["class_name"] = merged
            else:
                # If the function didn't ask for it, ensure it's removed
                kwargs.pop("class_name", None)

        # Standardize other React-like props
        if "htmlFor" in kwargs:
            kwargs["html_for"] = kwargs.pop("htmlFor")

        result = self.fn(*args, **kwargs)
        if isinstance(result, str) and not isinstance(result, Markup):
            return Markup(result)

        return result


def component(fn: Callable[..., str]) -> Component:
    """Decorator to mark and register a PulsePoint component"""
    return Component(fn)


def load_component_from_path(path: str, component_name: str, base_dir: str = "") -> Component | None:
    if path == '.' or path == './':
        full_path = os.path.join(
            base_dir, f"{component_name}.py") if base_dir else f"{component_name}.py"
    elif path.startswith('./') or path.startswith('../'):
        full_path = os.path.normpath(os.path.join(
            base_dir, path)) if base_dir else os.path.normpath(path)
    else:
        full_path = path

    if full_path.endswith('.py'):
        file_path = full_path
    elif os.path.isdir(full_path):
        file_path = os.path.join(full_path, f"{component_name}.py")
    else:
        file_path = f"{full_path}.py" if not os.path.isdir(
            full_path) else os.path.join(full_path, f"{component_name}.py")

    if not os.path.exists(file_path):
        return None

    try:
        cwd = os.getcwd()
        abs_file_path = os.path.abspath(file_path)
        if abs_file_path.startswith(cwd):
            rel_path = os.path.relpath(abs_file_path, cwd)
            if not rel_path.startswith('..'):
                module_name = os.path.splitext(
                    rel_path)[0].replace(os.sep, '.')
                module = importlib.import_module(module_name)
                comp = getattr(module, component_name, None)
                if isinstance(comp, Component):
                    comp.source_path = abs_file_path
                    return comp
    except (ImportError, ValueError, AttributeError):
        pass

    try:
        unique_module_name = f"pp_component_{os.path.abspath(file_path).replace(os.sep, '_').replace('.', '_')}"
        spec = importlib.util.spec_from_file_location(
            unique_module_name, file_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        comp = getattr(module, component_name, None)
        if isinstance(comp, Component):
            comp.source_path = file_path
            return comp
    except Exception as e:
        print(
            f"Error loading component {component_name} from {file_path}: {e}")
        return None

    return None


# ====
# TEMPLATE RENDERING (Jinja2 powered)
# ====

def render_html(file_path: str, **kwargs) -> str:
    """
    Load HTML template and render with Jinja2.
    """
    # Resolve file path relative to caller
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_file = frame.f_back.f_globals.get('__file__', '')
        if caller_file:
            base_dir = os.path.dirname(caller_file)
            full_path = os.path.join(base_dir, file_path)
        else:
            full_path = file_path
    else:
        full_path = file_path

    if full_path.endswith('.py'):
        full_path = full_path[:-3] + '.html'

    content = load_template_file(full_path)
    content = transpile_syntax(content)

    # 1. EXTRACT CHILDREN
    children_content = kwargs.pop("children", "")

    # 2. MARK CHILDREN AS SAFE
    # If children comes from another component (via the fix above), it's already Markup.
    # If it's a plain string, we trust it here (React children prop behavior).
    safe_children = Markup(children_content) if children_content else ""

    # 3. GENERATE ATTRIBUTES
    # Using your NEW get_attributes from html_attrs.py which returns Markup
    props_string = get_attributes(kwargs)

    # 4. RENDER
    template = env.from_string(content)
    return template.render(props=props_string, children=safe_children, **kwargs)


# ====
# EXPORTS
# ====

__all__ = [
    'Component',
    'component',
    'load_component_from_path',
    'render_html',
    '_component_registry',
]
