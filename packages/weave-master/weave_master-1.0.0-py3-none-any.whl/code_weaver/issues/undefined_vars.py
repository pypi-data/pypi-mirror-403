"""Undefined variable detection."""

import ast
import builtins
from typing import Any

from code_weaver.core.analyzer import BaseAnalyzer, ScopeTracker, find_similar_names
from code_weaver.issues.base import Issue, IssueType, Severity


# Built-in names that are always available
BUILTIN_NAMES = set(dir(builtins))

# Common module-level names that might be defined elsewhere
COMMON_GLOBALS = {
    "__name__", "__file__", "__doc__", "__package__",
    "__spec__", "__loader__", "__cached__", "__builtins__",
    "__annotations__", "__dict__",
}


class UndefinedVariableVisitor(ScopeTracker):
    """AST visitor that detects undefined variable usage."""

    def __init__(self, source_code: str, filepath: str):
        super().__init__()
        self.source_code = source_code
        self.filepath = filepath
        self.issues: list[Issue] = []
        self.imports: set[str] = set()
        self.deferred_checks: list[tuple[str, ast.AST]] = []

        # Pre-populate with builtins
        for name in BUILTIN_NAMES:
            self.define(name, None)
        for name in COMMON_GLOBALS:
            self.define(name, None)

    def visit_Import(self, node: ast.Import):
        """Handle import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split(".")[0]
            self.define(name, node)
            self.imports.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle from ... import statements."""
        for alias in node.names:
            if alias.name == "*":
                # Star import - we can't track these well
                continue
            name = alias.asname if alias.asname else alias.name
            self.define(name, node)
            self.imports.add(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle function definitions."""
        self.define(node.name, node)
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async function definitions."""
        self.define(node.name, node)
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        """Common handler for function definitions."""
        self.push_scope()

        # Define parameters
        for arg in node.args.args:
            self.define(arg.arg, arg)
        for arg in node.args.posonlyargs:
            self.define(arg.arg, arg)
        for arg in node.args.kwonlyargs:
            self.define(arg.arg, arg)
        if node.args.vararg:
            self.define(node.args.vararg.arg, node.args.vararg)
        if node.args.kwarg:
            self.define(node.args.kwarg.arg, node.args.kwarg)

        # Visit function body
        for child in node.body:
            self.visit(child)

        self.pop_scope()

    def visit_ClassDef(self, node: ast.ClassDef):
        """Handle class definitions."""
        self.define(node.name, node)
        self.push_scope()

        # Visit class body
        for child in node.body:
            self.visit(child)

        self.pop_scope()

    def visit_For(self, node: ast.For):
        """Handle for loops."""
        self._define_target(node.target)
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        """Handle with statements."""
        for item in node.items:
            if item.optional_vars:
                self._define_target(item.optional_vars)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Handle exception handlers."""
        if node.name:
            self.define(node.name, node)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """Handle assignment statements."""
        # First visit the value (right side)
        self.visit(node.value)

        # Then define targets (left side)
        for target in node.targets:
            self._define_target(target)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Handle annotated assignments."""
        if node.value:
            self.visit(node.value)
        self._define_target(node.target)

    def visit_AugAssign(self, node: ast.AugAssign):
        """Handle augmented assignments (+=, etc.)."""
        # The target must already be defined for augmented assignment
        self.visit(node.value)
        # Check if target is defined before augmented assignment
        if isinstance(node.target, ast.Name):
            self._check_name(node.target)
        self._define_target(node.target)

    def visit_NamedExpr(self, node: ast.NamedExpr):
        """Handle walrus operator (:=)."""
        self.visit(node.value)
        self.define(node.target.id, node)

    def visit_comprehension(self, node: ast.comprehension):
        """Handle comprehension iterators."""
        self._define_target(node.target)
        self.visit(node.iter)
        for if_clause in node.ifs:
            self.visit(if_clause)

    def visit_ListComp(self, node: ast.ListComp):
        """Handle list comprehensions."""
        self._visit_comprehension(node)

    def visit_SetComp(self, node: ast.SetComp):
        """Handle set comprehensions."""
        self._visit_comprehension(node)

    def visit_DictComp(self, node: ast.DictComp):
        """Handle dict comprehensions."""
        self.push_scope()
        for generator in node.generators:
            self.visit_comprehension(generator)
        self.visit(node.key)
        self.visit(node.value)
        self.pop_scope()

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        """Handle generator expressions."""
        self._visit_comprehension(node)

    def _visit_comprehension(self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp):
        """Common handler for comprehensions."""
        self.push_scope()
        for generator in node.generators:
            self.visit_comprehension(generator)
        self.visit(node.elt)
        self.pop_scope()

    def visit_Lambda(self, node: ast.Lambda):
        """Handle lambda expressions."""
        self.push_scope()
        for arg in node.args.args:
            self.define(arg.arg, arg)
        if node.args.vararg:
            self.define(node.args.vararg.arg, node.args.vararg)
        if node.args.kwarg:
            self.define(node.args.kwarg.arg, node.args.kwarg)
        self.visit(node.body)
        self.pop_scope()

    def visit_Global(self, node: ast.Global):
        """Handle global statements."""
        for name in node.names:
            self.global_names.add(name)
            # Define in current scope as referencing global
            self.define(name, node)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        """Handle nonlocal statements."""
        for name in node.names:
            self.nonlocal_names.add(name)
            # Should already be defined in enclosing scope
            if not self.is_defined(name):
                self.issues.append(Issue(
                    type=IssueType.UNDEFINED_VAR,
                    severity=Severity.ERROR,
                    filepath=self.filepath,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Nonlocal variable '{name}' not found in enclosing scope",
                    confidence=0.9,
                ))
            else:
                self.define(name, node)

    def visit_Name(self, node: ast.Name):
        """Handle name references."""
        if isinstance(node.ctx, ast.Load):
            self._check_name(node)
        elif isinstance(node.ctx, ast.Store):
            self.define(node.id, node)
        self.generic_visit(node)

    def _check_name(self, node: ast.Name):
        """Check if a name is defined."""
        name = node.id
        if not self.is_defined(name):
            # Find similar names for suggestions
            all_names = self.get_all_defined_names() | self.imports
            similar = find_similar_names(name, all_names)

            suggested_fix = None
            confidence = 0.8

            if similar:
                suggested_fix = similar[0]
                confidence = 0.85

            self.issues.append(Issue(
                type=IssueType.UNDEFINED_VAR,
                severity=Severity.ERROR,
                filepath=self.filepath,
                line=node.lineno,
                column=node.col_offset,
                message=f"Undefined variable '{name}'",
                suggested_fix=suggested_fix,
                confidence=confidence,
                context={
                    "name": name,
                    "similar_names": similar[:3],
                },
            ))

    def _define_target(self, target: ast.AST):
        """Define variables from an assignment target."""
        if isinstance(target, ast.Name):
            self.define(target.id, target)
        elif isinstance(target, ast.Tuple | ast.List):
            for elt in target.elts:
                self._define_target(elt)
        elif isinstance(target, ast.Starred):
            self._define_target(target.value)
        # Attribute and Subscript targets don't define new names


class UndefinedVariableAnalyzer(BaseAnalyzer):
    """Analyzer for detecting undefined variable usage."""

    def detect(self, tree: ast.AST, source_code: str, filepath: str) -> list[Issue]:
        """Detect undefined variables in the AST."""
        visitor = UndefinedVariableVisitor(source_code, filepath)
        visitor.visit(tree)
        return visitor.issues
