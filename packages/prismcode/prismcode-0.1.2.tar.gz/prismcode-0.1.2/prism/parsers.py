"""Parsing strategies for extracting dependencies from different file types."""
import ast
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Set, Tuple, Optional, FrozenSet
from functools import lru_cache

from .models import EdgeType


class ParserStrategy(ABC):
    """Abstract base class for file parsing strategies."""

    @abstractmethod
    def parse(self, file_path: Path, project_root: Path) -> List[Tuple[str, EdgeType]]:
        """Parse a file and return list of (reference, edge_type) tuples.

        Args:
            file_path: Absolute path to the file to parse
            project_root: Root directory of the project

        Returns:
            List of (reference_string, edge_type) tuples
        """
        pass


class PythonParser(ParserStrategy):
    """Parser for Python files using AST analysis."""

    def __init__(self, project_packages: FrozenSet[str] = frozenset()):
        """Initialize parser with known project packages.

        Args:
            project_packages: Set of top-level package names in the project
        """
        self.project_packages = project_packages

    def parse(self, file_path: Path, project_root: Path) -> List[Tuple[str, EdgeType]]:
        """Parse Python file for imports and dependencies."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            return []

        extractor = _ImportExtractor(self.project_packages, file_path, project_root)
        extractor.visit(tree)

        results = []

        # Static imports
        for imp in extractor.imports:
            results.append((imp, EdgeType.IMPORT))

        # Dynamic imports
        for imp in extractor.dynamic_imports:
            results.append((imp, EdgeType.DYNAMIC_IMPORT))

        # String references
        for imp in extractor.potential_modules:
            results.append((imp, EdgeType.STRING_REF))

        # Template references (Flask/FastAPI)
        for tmpl in extractor.template_refs:
            results.append((tmpl, EdgeType.TEMPLATE))

        return results


class _ImportExtractor(ast.NodeVisitor):
    """AST visitor to extract imports and references from Python code."""

    def __init__(self, project_packages: FrozenSet[str], file_path: Path = None, project_root: Path = None):
        self.imports: Set[str] = set()
        self.dynamic_imports: Set[str] = set()
        self.potential_modules: Set[str] = set()
        self.template_refs: Set[str] = set()
        self.project_packages = project_packages
        self.file_path = file_path
        self.project_root = project_root

    def visit_Import(self, node):
        """Extract from: import foo"""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Extract from: from foo import bar"""
        if node.level > 0 and self.file_path and self.project_root:
            # Relative import - resolve to absolute module path
            base_package = self._get_package_from_path(node.level)
            if base_package:
                if node.module:
                    # from .foo import bar -> package.foo
                    abs_module = f"{base_package}.{node.module}"
                else:
                    # from . import bar -> package
                    abs_module = base_package
                self.imports.add(abs_module)
                # Also add module.name for cases where bar is a submodule
                for alias in node.names:
                    if alias.name != "*":
                        full_path = f"{abs_module}.{alias.name}"
                        self.imports.add(full_path)
        elif node.module:
            # Absolute import
            self.imports.add(node.module)
            # Also add "module.name" for submodules
            # e.g., "from backend.routers import auth" -> "backend.routers.auth"
            for alias in node.names:
                if alias.name != "*":
                    full_path = f"{node.module}.{alias.name}"
                    self.imports.add(full_path)
        self.generic_visit(node)

    def _get_package_from_path(self, level: int) -> Optional[str]:
        """Convert file path to package name, going up 'level' directories.

        level=1 means current package (the directory the file is in)
        level=2 means parent package (go up one directory)
        level=n means go up (n-1) directories
        """
        if not self.file_path or not self.project_root:
            return None
        try:
            rel_path = self.file_path.relative_to(self.project_root)
            parts = list(rel_path.parts[:-1])  # Remove filename, get directory = package
            # level=1 is current package, level=2 is parent, etc.
            # So we go up (level - 1) directories
            levels_up = level - 1
            if levels_up > 0:
                parts = parts[:-levels_up] if levels_up < len(parts) else []
            return ".".join(parts) if parts else None
        except ValueError:
            return None

    def visit_Call(self, node):
        """Extract dynamic imports and template references."""
        func = node.func

        # Dynamic imports: importlib.import_module(), __import__()
        is_import_module = False
        if isinstance(func, ast.Attribute) and func.attr == "import_module":
            if isinstance(func.value, ast.Name) and func.value.id == "importlib":
                is_import_module = True
        if isinstance(func, ast.Name) and func.id in ("import_module", "__import__"):
            is_import_module = True

        func_name = None
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr

        # Custom loader functions
        loader_functions = [
            "load_tools_from_toolbox",
            "import_module",
            "load_module",
            "__import__",
        ]

        if (is_import_module or func_name in loader_functions) and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                self.dynamic_imports.add(first_arg.value)

        # Flask/FastAPI template references
        if func_name in ("render_template", "render_template_string"):
            if node.args and isinstance(node.args[0], ast.Constant):
                template_name = node.args[0].value
                if isinstance(template_name, str):
                    self.template_refs.add(template_name)

        # FileResponse (FastAPI pattern)
        if func_name == "FileResponse":
            if node.args:
                html_path = self._extract_html_path(node.args[0])
                if html_path:
                    self.template_refs.add(html_path)

        self.generic_visit(node)

    def visit_Constant(self, node):
        """Extract potential module references from string constants."""
        if isinstance(node.value, str):
            value = node.value
            if "." in value and not value.startswith("."):
                for pkg in self.project_packages:
                    if value.startswith(pkg + ".") or value == pkg:
                        self.potential_modules.add(value)
                        break
        self.generic_visit(node)

    def _extract_html_path(self, node) -> Optional[str]:
        """Extract HTML file path from AST node."""
        # Simple string constant
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.endswith(('.html', '.htm')):
                return node.value
            return None

        # str(path)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "str":
                if node.args:
                    return self._extract_html_path(node.args[0])

        # Path / operation
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            right = node.right
            if isinstance(right, ast.Constant) and isinstance(right.value, str):
                if right.value.endswith(('.html', '.htm')):
                    return right.value
            if isinstance(right, ast.BinOp):
                return self._extract_html_path(right)

        return None


class HTMLParser(ParserStrategy):
    """Parser for HTML/Jinja2 template files."""

    def parse(self, file_path: Path, project_root: Path) -> List[Tuple[str, EdgeType]]:
        """Parse HTML file for dependencies."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        results = []

        # Script tags: <script src="...">
        script_pattern = r'<script[^>]+src=["\']([^"\']+)["\']'
        for match in re.finditer(script_pattern, content, re.IGNORECASE):
            ref = match.group(1)
            if self._is_local_ref(ref):
                results.append((ref, EdgeType.SCRIPT))

        # Link tags for stylesheets
        link_pattern = r'<link[^>]+href=["\']([^"\']+)["\']'
        for match in re.finditer(link_pattern, content, re.IGNORECASE):
            ref = match.group(1)
            if self._is_local_ref(ref) and ref.endswith('.css'):
                results.append((ref, EdgeType.STYLESHEET))

        # Flask url_for static references
        url_for_pattern = r'{{\s*url_for\s*\(\s*["\']static["\']\s*,\s*filename\s*=\s*["\']([^"\']+)["\']\s*\)\s*}}'
        for match in re.finditer(url_for_pattern, content):
            ref = match.group(1)
            if ref.endswith(('.js', '.jsx', '.ts', '.tsx')):
                results.append((f"static/{ref}", EdgeType.SCRIPT))
            elif ref.endswith(('.css', '.scss', '.less')):
                results.append((f"static/{ref}", EdgeType.STYLESHEET))

        # Jinja includes: {% include '...' %}
        include_pattern = r'{%\s*include\s+["\']([^"\']+)["\']\s*%}'
        for match in re.finditer(include_pattern, content):
            results.append((match.group(1), EdgeType.INCLUDE))

        # Jinja extends: {% extends '...' %}
        extends_pattern = r'{%\s*extends\s+["\']([^"\']+)["\']\s*%}'
        for match in re.finditer(extends_pattern, content):
            results.append((match.group(1), EdgeType.EXTENDS))

        # Jinja from imports: {% from '...' import ... %}
        from_pattern = r'{%\s*from\s+["\']([^"\']+)["\']\s+import'
        for match in re.finditer(from_pattern, content):
            results.append((match.group(1), EdgeType.INCLUDE))

        return results

    def _is_local_ref(self, ref: str) -> bool:
        """Check if reference is local (not external URL)."""
        return not ref.startswith(("http://", "https://", "//", "data:", "blob:"))


class JavaScriptParser(ParserStrategy):
    """Parser for JavaScript/TypeScript files."""

    def parse(self, file_path: Path, project_root: Path) -> List[Tuple[str, EdgeType]]:
        """Parse JS file for imports."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        results = []

        # ES6 imports: import ... from '...' (handles multi-line imports)
        import_from_pattern = r'import\s+[\s\S]*?\s+from\s+["\']([^"\']+)["\']'
        for match in re.finditer(import_from_pattern, content):
            ref = match.group(1)
            if self._is_local_ref(ref):
                results.append((ref, EdgeType.JS_IMPORT))

        # Direct imports: import '...'
        import_direct_pattern = r'import\s+["\']([^"\']+)["\']'
        for match in re.finditer(import_direct_pattern, content):
            ref = match.group(1)
            if self._is_local_ref(ref):
                results.append((ref, EdgeType.JS_IMPORT))

        # Dynamic imports: import('...')
        dynamic_pattern = r'import\s*\(\s*["\']([^"\']+)["\']\s*\)'
        for match in re.finditer(dynamic_pattern, content):
            ref = match.group(1)
            if self._is_local_ref(ref):
                results.append((ref, EdgeType.JS_IMPORT))

        # CommonJS requires: require('...')
        require_pattern = r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'
        for match in re.finditer(require_pattern, content):
            ref = match.group(1)
            if self._is_local_ref(ref):
                results.append((ref, EdgeType.JS_IMPORT))

        return results

    def _is_local_ref(self, ref: str) -> bool:
        """Check if reference is local (starts with ./ or ../)."""
        return ref.startswith((".", "/"))


class CSSParser(ParserStrategy):
    """Parser for CSS files."""

    def parse(self, file_path: Path, project_root: Path) -> List[Tuple[str, EdgeType]]:
        """Parse CSS file for @import rules."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        results = []

        # @import rules: @import '...' or @import url('...')
        import_pattern = r'@import\s+(?:url\s*\(\s*)?["\']?([^"\')\s;]+)["\']?\s*\)?'
        for match in re.finditer(import_pattern, content):
            ref = match.group(1)
            if self._is_local_ref(ref) and ref.endswith('.css'):
                results.append((ref, EdgeType.CSS_IMPORT))

        return results

    def _is_local_ref(self, ref: str) -> bool:
        """Check if reference is local."""
        return not ref.startswith(("http://", "https://", "//", "data:"))


class PathResolver:
    """Resolves file references to actual file paths."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def resolve_python_import(
        self,
        import_str: str,
        source_file: Path,
        all_files: Set[Path]
    ) -> List[Path]:
        """Resolve a Python import string to possible file paths.

        Args:
            import_str: The import string (e.g., "backend.api.routes")
            source_file: The file containing the import
            all_files: Set of all files in the project

        Returns:
            List of resolved file paths (including intermediate __init__.py files)
        """
        parts = import_str.split(".")
        possibilities = []

        # Try as package
        possibilities.append(self.project_root / "/".join(parts) / "__init__.py")
        # Try as module
        possibilities.append(self.project_root / (("/".join(parts)) + ".py"))

        # Also add all intermediate __init__.py files in the package chain
        # e.g., for "zdeps2.core.config", also add zdeps2/__init__.py, zdeps2/core/__init__.py
        for i in range(1, len(parts)):
            intermediate_path = self.project_root / "/".join(parts[:i]) / "__init__.py"
            possibilities.append(intermediate_path)

        # Try relative to source file
        source_dir = source_file.parent
        possibilities.append(source_dir / "/".join(parts) / "__init__.py")
        possibilities.append(source_dir / (("/".join(parts)) + ".py"))

        # Try parent directories
        for i in range(1, min(5, len(source_dir.parts))):
            parent = source_dir.parents[i - 1] if i <= len(source_dir.parents) else None
            if parent:
                possibilities.append(parent / "/".join(parts) / "__init__.py")
                possibilities.append(parent / (("/".join(parts)) + ".py"))

        # Filter to existing files
        resolved = []
        for path in possibilities:
            try:
                resolved_path = path.resolve()
                if resolved_path in all_files:
                    resolved.append(resolved_path)
            except (ValueError, OSError):
                pass

        return resolved

    def resolve_template(
        self,
        template_ref: str,
        source_file: Path,
        template_folder: Optional[Path] = None,
        static_folder: Optional[Path] = None
    ) -> Optional[Path]:
        """Resolve a template reference to actual file path.

        Uses the source file's location to find the correct template,
        walking up the directory tree to find templates/ folder.
        This works for Flask, Django, FastAPI, etc.
        """
        # Walk up from source file's directory, looking for templates/
        current = source_file.parent
        while current != self.project_root.parent:
            # Check templates/ subfolder
            candidate = current / "templates" / template_ref
            try:
                if candidate.exists():
                    return candidate.resolve()
            except (ValueError, OSError):
                pass

            # Move up one level
            if current == self.project_root or current.parent == current:
                break
            current = current.parent

        # Fallback: try explicit template_folder if provided
        if template_folder:
            candidate = template_folder / template_ref
            try:
                if candidate.exists():
                    return candidate.resolve()
            except (ValueError, OSError):
                pass

        return None

    def resolve_frontend_ref(
        self,
        ref: str,
        source_file: Path,
        static_folder: Optional[Path] = None
    ) -> Optional[Path]:
        """Resolve a frontend file reference (JS/CSS) to actual path.

        Uses the source file's location to find the correct static folder,
        walking up the directory tree.
        """
        # Clean the reference - remove /static/ prefix if present
        clean_ref = ref
        for prefix in ["/static/", "static/", "/assets/", "assets/"]:
            if ref.startswith(prefix):
                clean_ref = ref[len(prefix):]
                break

        # Try relative to source file first (for "./foo.js" style refs)
        if ref.startswith("."):
            candidate = (source_file.parent / ref).resolve()
            try:
                if candidate.exists():
                    return candidate
            except (ValueError, OSError):
                pass

        # Walk up from source file's directory, looking for static/
        current = source_file.parent
        while current != self.project_root.parent:
            # Check static/ subfolder
            candidate = current / "static" / clean_ref
            try:
                if candidate.exists():
                    return candidate.resolve()
            except (ValueError, OSError):
                pass

            # Move up one level
            if current == self.project_root or current.parent == current:
                break
            current = current.parent

        # Fallback: try explicit static_folder if provided
        if static_folder:
            candidate = static_folder / clean_ref
            try:
                if candidate.exists():
                    return candidate.resolve()
            except (ValueError, OSError):
                pass

        return None
