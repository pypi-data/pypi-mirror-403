"""Type error detection."""

import ast
from typing import Any

from code_weaver.core.analyzer import BaseAnalyzer, get_source_segment
from code_weaver.issues.base import Issue, IssueType, Severity


# Basic type inference mapping
LITERAL_TYPES = {
    ast.Constant: lambda node: type(node.value).__name__ if node.value is not None else "NoneType",
    ast.List: lambda _: "list",
    ast.Tuple: lambda _: "tuple",
    ast.Dict: lambda _: "dict",
    ast.Set: lambda _: "set",
}

# Operations that are invalid between certain types
INVALID_BINOPS = {
    # (left_type, op_type, right_type) -> error message
    ("str", ast.Add, "int"): "Cannot concatenate str and int",
    ("int", ast.Add, "str"): "Cannot concatenate int and str",
    ("str", ast.Sub, "str"): "Cannot subtract strings",
    ("str", ast.Sub, "int"): "Cannot subtract int from str",
    ("str", ast.Mult, "str"): "Cannot multiply str by str",
    ("list", ast.Add, "int"): "Cannot add int to list",
    ("dict", ast.Add, "dict"): "Cannot add dictionaries (use | or .update())",
    ("set", ast.Add, "set"): "Cannot add sets (use | or .union())",
}

# Type hints mapping
TYPE_HINT_NAMES = {
    "int": "int",
    "str": "str",
    "float": "float",
    "bool": "bool",
    "list": "list",
    "dict": "dict",
    "set": "set",
    "tuple": "tuple",
    "List": "list",
    "Dict": "dict",
    "Set": "set",
    "Tuple": "tuple",
    "Optional": "Optional",
    "Union": "Union",
    "None": "NoneType",
}


class TypeInferenceVisitor(ast.NodeVisitor):
    """AST visitor that performs basic type inference."""

    def __init__(self, source_code: str, filepath: str):
        self.source_code = source_code
        self.filepath = filepath
        self.issues: list[Issue] = []
        self.variable_types: dict[str, str] = {}
        self.function_return_types: dict[str, str] = {}

    def infer_type(self, node: ast.AST) -> str | None:
        """Infer the type of an expression."""
        if isinstance(node, ast.Constant):
            if node.value is None:
                return "NoneType"
            return type(node.value).__name__

        if isinstance(node, ast.List):
            return "list"
        if isinstance(node, ast.Tuple):
            return "tuple"
        if isinstance(node, ast.Dict):
            return "dict"
        if isinstance(node, ast.Set):
            return "set"

        if isinstance(node, ast.Name):
            return self.variable_types.get(node.id)

        if isinstance(node, ast.Call):
            # Check for known constructors
            if isinstance(node.func, ast.Name):
                if node.func.id in ("int", "str", "float", "bool", "list", "dict", "set", "tuple"):
                    return node.func.id
            return None

        if isinstance(node, ast.BinOp):
            left_type = self.infer_type(node.left)
            right_type = self.infer_type(node.right)

            # String concatenation
            if left_type == "str" and right_type == "str" and isinstance(node.op, ast.Add):
                return "str"

            # Numeric operations
            if left_type in ("int", "float") and right_type in ("int", "float"):
                if "float" in (left_type, right_type):
                    return "float"
                if isinstance(node.op, ast.Div):
                    return "float"
                return "int"

            # List concatenation
            if left_type == "list" and right_type == "list" and isinstance(node.op, ast.Add):
                return "list"

            # String multiplication
            if left_type == "str" and right_type == "int" and isinstance(node.op, ast.Mult):
                return "str"

        if isinstance(node, ast.JoinedStr):
            return "str"

        if isinstance(node, ast.FormattedValue):
            return "str"

        return None

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Handle annotated assignments to track types."""
        if isinstance(node.target, ast.Name):
            type_name = self._extract_type_name(node.annotation)
            if type_name:
                self.variable_types[node.target.id] = type_name
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """Handle assignments to infer types."""
        inferred_type = self.infer_type(node.value)
        if inferred_type:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.variable_types[target.id] = inferred_type
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function return types from annotations."""
        if node.returns:
            return_type = self._extract_type_name(node.returns)
            if return_type:
                self.function_return_types[node.name] = return_type

        # Track parameter types
        for arg in node.args.args:
            if arg.annotation:
                type_name = self._extract_type_name(arg.annotation)
                if type_name:
                    self.variable_types[arg.arg] = type_name

        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        """Check for type errors in binary operations."""
        left_type = self.infer_type(node.left)
        right_type = self.infer_type(node.right)

        if left_type and right_type:
            # Check for known invalid operations
            op_type = type(node.op)
            key = (left_type, op_type, right_type)

            if key in INVALID_BINOPS:
                source = get_source_segment(self.source_code, node)
                self.issues.append(Issue(
                    type=IssueType.TYPE_ERROR,
                    severity=Severity.ERROR,
                    filepath=self.filepath,
                    line=node.lineno,
                    column=node.col_offset,
                    message=INVALID_BINOPS[key],
                    suggested_fix=self._suggest_fix(node, left_type, right_type),
                    confidence=0.9,
                    context={
                        "left_type": left_type,
                        "right_type": right_type,
                        "operation": op_type.__name__,
                        "source": source,
                    },
                ))

        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        """Check for type errors in comparisons."""
        # Most comparisons are valid between any types in Python
        # Focus on obvious mistakes
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Check for type errors in function calls."""
        # Check for common mistakes like len() on non-sequences
        if isinstance(node.func, ast.Name):
            func_name = node.func.id

            if func_name == "len" and node.args:
                arg_type = self.infer_type(node.args[0])
                if arg_type in ("int", "float", "bool"):
                    self.issues.append(Issue(
                        type=IssueType.TYPE_ERROR,
                        severity=Severity.ERROR,
                        filepath=self.filepath,
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"len() argument cannot be '{arg_type}'",
                        confidence=0.9,
                        context={"arg_type": arg_type},
                    ))

        self.generic_visit(node)

    def _extract_type_name(self, annotation: ast.AST) -> str | None:
        """Extract a simple type name from an annotation."""
        if isinstance(annotation, ast.Name):
            return TYPE_HINT_NAMES.get(annotation.id, annotation.id)
        if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            # String annotation
            return TYPE_HINT_NAMES.get(annotation.value, annotation.value)
        if isinstance(annotation, ast.Subscript):
            # Generic like List[int] - just get the base
            if isinstance(annotation.value, ast.Name):
                return TYPE_HINT_NAMES.get(annotation.value.id, annotation.value.id)
        return None

    def _suggest_fix(self, node: ast.BinOp, left_type: str, right_type: str) -> str | None:
        """Suggest a fix for a type error."""
        if left_type == "str" and right_type == "int" and isinstance(node.op, ast.Add):
            return "Convert int to str: str(value)"
        if left_type == "int" and right_type == "str" and isinstance(node.op, ast.Add):
            return "Convert str to int: int(value) or convert int to str: str(value)"
        if left_type == "dict" and right_type == "dict" and isinstance(node.op, ast.Add):
            return "Use {**dict1, **dict2} or dict1 | dict2 (Python 3.9+)"
        if left_type == "set" and right_type == "set" and isinstance(node.op, ast.Add):
            return "Use set1 | set2 or set1.union(set2)"
        return None


class TypeErrorAnalyzer(BaseAnalyzer):
    """Analyzer for detecting basic type errors."""

    def detect(self, tree: ast.AST, source_code: str, filepath: str) -> list[Issue]:
        """Detect type errors in the AST."""
        visitor = TypeInferenceVisitor(source_code, filepath)
        visitor.visit(tree)
        return visitor.issues
