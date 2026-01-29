"""Unused import detection."""

import ast
from dataclasses import dataclass

from code_weaver.core.analyzer import BaseAnalyzer, get_line_content
from code_weaver.issues.base import Issue, IssueType, Severity


@dataclass
class ImportInfo:
    """Information about an import statement."""
    name: str  # The name as it's used in code
    module: str  # The full module path
    node: ast.Import | ast.ImportFrom
    line: int
    column: int
    is_from_import: bool
    alias: str | None = None


class ImportCollector(ast.NodeVisitor):
    """Collect all imports from an AST."""

    def __init__(self):
        self.imports: dict[str, ImportInfo] = {}

    def visit_Import(self, node: ast.Import):
        """Handle import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split(".")[0]
            self.imports[name] = ImportInfo(
                name=name,
                module=alias.name,
                node=node,
                line=node.lineno,
                column=node.col_offset,
                is_from_import=False,
                alias=alias.asname,
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle from ... import statements."""
        module = node.module or ""
        for alias in node.names:
            if alias.name == "*":
                # Can't track star imports
                continue
            name = alias.asname if alias.asname else alias.name
            full_module = f"{module}.{alias.name}" if module else alias.name
            self.imports[name] = ImportInfo(
                name=name,
                module=full_module,
                node=node,
                line=node.lineno,
                column=node.col_offset,
                is_from_import=True,
                alias=alias.asname,
            )
        self.generic_visit(node)


class NameUsageCollector(ast.NodeVisitor):
    """Collect all name usages (excluding imports and definitions)."""

    def __init__(self):
        self.used_names: set[str] = set()
        self._in_import = False

    def visit_Import(self, node: ast.Import):
        """Skip import statements."""
        pass

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Skip from import statements."""
        pass

    def visit_Name(self, node: ast.Name):
        """Track name usage."""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Track attribute access."""
        # Get the root name of attribute chains
        root = node
        while isinstance(root, ast.Attribute):
            root = root.value

        if isinstance(root, ast.Name):
            self.used_names.add(root.id)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle function definitions including decorators and annotations."""
        # Visit decorators
        for decorator in node.decorator_list:
            self.visit(decorator)

        # Visit annotations
        if node.returns:
            self.visit(node.returns)

        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if arg.annotation:
                self.visit(arg.annotation)

        # Visit defaults
        for default in node.args.defaults + node.args.kw_defaults:
            if default:
                self.visit(default)

        # Visit body
        for child in node.body:
            self.visit(child)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async function definitions."""
        self.visit_FunctionDef(node)  # Same logic

    def visit_ClassDef(self, node: ast.ClassDef):
        """Handle class definitions including bases and decorators."""
        for decorator in node.decorator_list:
            self.visit(decorator)

        for base in node.bases:
            self.visit(base)

        for keyword in node.keywords:
            self.visit(keyword.value)

        for child in node.body:
            self.visit(child)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Handle annotated assignments."""
        self.visit(node.annotation)
        if node.value:
            self.visit(node.value)


class UnusedImportAnalyzer(BaseAnalyzer):
    """Analyzer for detecting unused imports."""

    # Imports that are commonly used for side effects or re-exports
    ALLOWED_UNUSED = {
        "__future__",
    }

    def detect(self, tree: ast.AST, source_code: str, filepath: str) -> list[Issue]:
        """Detect unused imports in the AST."""
        # Collect all imports
        import_collector = ImportCollector()
        import_collector.visit(tree)

        # Collect all name usages
        usage_collector = NameUsageCollector()
        usage_collector.visit(tree)

        issues = []

        for name, import_info in import_collector.imports.items():
            # Check if import is used
            if name not in usage_collector.used_names:
                # Skip allowed unused imports
                if any(allowed in import_info.module for allowed in self.ALLOWED_UNUSED):
                    continue

                # Generate fix suggestion (remove the import line)
                line_content = get_line_content(source_code, import_info.line)
                suggested_fix = self._generate_fix(import_info, source_code)

                issues.append(Issue(
                    type=IssueType.UNUSED_IMPORT,
                    severity=Severity.WARNING,
                    filepath=filepath,
                    line=import_info.line,
                    column=import_info.column,
                    message=f"Unused import '{name}'",
                    suggested_fix=suggested_fix,
                    confidence=0.95,  # High confidence - unused imports are safe to remove
                    context={
                        "name": name,
                        "module": import_info.module,
                        "is_from_import": import_info.is_from_import,
                        "line_content": line_content.strip(),
                    },
                ))

        return issues

    def _generate_fix(self, import_info: ImportInfo, source_code: str) -> str:
        """Generate a fix suggestion for removing the unused import."""
        line_content = get_line_content(source_code, import_info.line)

        if import_info.is_from_import:
            # For from imports, we might need to just remove one name
            node = import_info.node
            if isinstance(node, ast.ImportFrom) and len(node.names) > 1:
                # Multiple imports on same line - just suggest removing this name
                return f"Remove '{import_info.name}' from import"
            else:
                return f"Remove line: {line_content.strip()}"
        else:
            # For regular imports
            node = import_info.node
            if isinstance(node, ast.Import) and len(node.names) > 1:
                return f"Remove '{import_info.name}' from import"
            else:
                return f"Remove line: {line_content.strip()}"
