"""Syntax issue detection."""

import ast
import re
import tokenize
from io import StringIO

from code_weaver.core.analyzer import BaseAnalyzer, get_line_content
from code_weaver.issues.base import Issue, IssueType, Severity


class SyntaxIssueAnalyzer(BaseAnalyzer):
    """Analyzer for detecting syntax issues and common mistakes."""

    def detect(self, tree: ast.AST, source_code: str, filepath: str) -> list[Issue]:
        """Detect syntax issues in the source code."""
        issues = []

        # Check for various syntax patterns
        issues.extend(self._check_fstring_issues(source_code, filepath))
        issues.extend(self._check_indentation_issues(source_code, filepath))
        issues.extend(self._check_bracket_issues(source_code, filepath))
        issues.extend(self._check_common_mistakes(source_code, filepath))
        issues.extend(self._check_ast_issues(tree, source_code, filepath))

        return issues

    def _check_fstring_issues(self, source_code: str, filepath: str) -> list[Issue]:
        """Check for f-string issues."""
        issues = []
        lines = source_code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for empty braces in f-strings
            fstring_pattern = r'f["\'].*\{\s*\}.*["\']'
            if re.search(fstring_pattern, line):
                issues.append(Issue(
                    type=IssueType.SYNTAX_ISSUE,
                    severity=Severity.ERROR,
                    filepath=filepath,
                    line=line_num,
                    column=0,
                    message="Empty braces in f-string",
                    suggested_fix="Add an expression inside the braces",
                    confidence=0.95,
                    context={"line_content": line.strip()},
                ))

            # Check for unmatched braces in f-strings
            if re.match(r'.*f["\']', line):
                # Count braces (simple check, doesn't handle nested strings)
                in_fstring = False
                brace_count = 0
                i = 0
                while i < len(line):
                    if line[i:i+2] in ('f"', "f'"):
                        in_fstring = True
                        i += 2
                        continue
                    if in_fstring:
                        if line[i] == '{' and (i + 1 >= len(line) or line[i+1] != '{'):
                            brace_count += 1
                        elif line[i] == '}' and (i + 1 >= len(line) or line[i+1] != '}'):
                            brace_count -= 1
                        elif line[i] in '"\'':
                            in_fstring = False
                    i += 1

                if brace_count != 0:
                    issues.append(Issue(
                        type=IssueType.SYNTAX_ISSUE,
                        severity=Severity.ERROR,
                        filepath=filepath,
                        line=line_num,
                        column=0,
                        message="Unmatched braces in f-string",
                        suggested_fix="Check brace matching in f-string",
                        confidence=0.8,
                        context={"line_content": line.strip()},
                    ))

        return issues

    def _check_indentation_issues(self, source_code: str, filepath: str) -> list[Issue]:
        """Check for indentation issues."""
        issues = []
        lines = source_code.splitlines()

        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue

            # Check for mixed tabs and spaces
            leading = line[:len(line) - len(line.lstrip())]
            if '\t' in leading and ' ' in leading:
                issues.append(Issue(
                    type=IssueType.SYNTAX_ISSUE,
                    severity=Severity.WARNING,
                    filepath=filepath,
                    line=line_num,
                    column=0,
                    message="Mixed tabs and spaces in indentation",
                    suggested_fix="Use consistent indentation (prefer 4 spaces)",
                    confidence=0.9,
                    context={"line_content": line.strip()},
                ))

        return issues

    def _check_bracket_issues(self, source_code: str, filepath: str) -> list[Issue]:
        """Check for bracket matching issues."""
        issues = []

        # Use tokenize to properly handle strings and comments
        try:
            tokens = list(tokenize.generate_tokens(StringIO(source_code).readline))
        except tokenize.TokenError:
            # Tokenization failed - likely a syntax error
            return issues

        bracket_stack: list[tuple[str, int, int]] = []
        brackets = {'(': ')', '[': ']', '{': '}'}
        closing = {')': '(', ']': '[', '}': '{'}

        for token in tokens:
            if token.type == tokenize.OP:
                if token.string in brackets:
                    bracket_stack.append((token.string, token.start[0], token.start[1]))
                elif token.string in closing:
                    if not bracket_stack:
                        issues.append(Issue(
                            type=IssueType.SYNTAX_ISSUE,
                            severity=Severity.ERROR,
                            filepath=filepath,
                            line=token.start[0],
                            column=token.start[1],
                            message=f"Unmatched closing bracket '{token.string}'",
                            suggested_fix=f"Remove unmatched '{token.string}' or add matching '{closing[token.string]}'",
                            confidence=0.95,
                        ))
                    elif bracket_stack[-1][0] != closing[token.string]:
                        expected = brackets[bracket_stack[-1][0]]
                        issues.append(Issue(
                            type=IssueType.SYNTAX_ISSUE,
                            severity=Severity.ERROR,
                            filepath=filepath,
                            line=token.start[0],
                            column=token.start[1],
                            message=f"Mismatched bracket: expected '{expected}', got '{token.string}'",
                            suggested_fix=f"Replace '{token.string}' with '{expected}'",
                            confidence=0.9,
                        ))
                    else:
                        bracket_stack.pop()

        # Check for unclosed brackets
        for bracket, line, col in bracket_stack:
            issues.append(Issue(
                type=IssueType.SYNTAX_ISSUE,
                severity=Severity.ERROR,
                filepath=filepath,
                line=line,
                column=col,
                message=f"Unclosed bracket '{bracket}'",
                suggested_fix=f"Add closing '{brackets[bracket]}'",
                confidence=0.95,
            ))

        return issues

    def _check_common_mistakes(self, source_code: str, filepath: str) -> list[Issue]:
        """Check for common Python mistakes."""
        issues = []
        lines = source_code.splitlines()

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for = instead of == in comparisons
            # Simple heuristic: if/while/elif followed by assignment
            if re.match(r'^(if|while|elif)\s+.*[^=!<>]=(?!=)', stripped):
                # More careful check to avoid false positives
                match = re.search(r'(if|while|elif)\s+(.+):', stripped)
                if match:
                    condition = match.group(2)
                    # Check for single = not preceded/followed by =, <, >, !
                    if re.search(r'(?<![=!<>])=(?!=)', condition):
                        # Exclude walrus operator :=
                        if ':=' not in condition:
                            issues.append(Issue(
                                type=IssueType.SYNTAX_ISSUE,
                                severity=Severity.WARNING,
                                filepath=filepath,
                                line=line_num,
                                column=0,
                                message="Possible assignment instead of comparison (= vs ==)",
                                suggested_fix="Use == for comparison",
                                confidence=0.7,
                                context={"line_content": stripped},
                            ))

            # Check for missing colon after control statements
            control_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with', 'def', 'class']
            for keyword in control_keywords:
                if stripped.startswith(keyword + ' ') or stripped == keyword:
                    if not stripped.endswith(':') and not stripped.endswith('\\'):
                        # Check if this is a multi-line statement
                        if '(' not in stripped or stripped.count('(') == stripped.count(')'):
                            if '[' not in stripped or stripped.count('[') == stripped.count(']'):
                                issues.append(Issue(
                                    type=IssueType.SYNTAX_ISSUE,
                                    severity=Severity.HINT,
                                    filepath=filepath,
                                    line=line_num,
                                    column=len(stripped),
                                    message=f"Missing colon after '{keyword}' statement",
                                    suggested_fix="Add ':' at the end of the line",
                                    confidence=0.6,
                                    context={"line_content": stripped},
                                ))
                        break

            # Check for print statements (Python 2 style)
            if re.match(r'^print\s+[^(]', stripped) and not stripped.startswith('print('):
                issues.append(Issue(
                    type=IssueType.SYNTAX_ISSUE,
                    severity=Severity.ERROR,
                    filepath=filepath,
                    line=line_num,
                    column=0,
                    message="Python 2 style print statement",
                    suggested_fix="Use print() function: print(...)",
                    confidence=0.95,
                    context={"line_content": stripped},
                ))

        return issues

    def _check_ast_issues(self, tree: ast.AST, source_code: str, filepath: str) -> list[Issue]:
        """Check for issues detectable through AST analysis."""
        issues = []

        class ASTChecker(ast.NodeVisitor):
            def visit_Assert(self, node):
                """Check for assertions with side effects."""
                # Check if assert is used with a tuple (common mistake)
                if isinstance(node.test, ast.Tuple):
                    issues.append(Issue(
                        type=IssueType.SYNTAX_ISSUE,
                        severity=Severity.WARNING,
                        filepath=filepath,
                        line=node.lineno,
                        column=node.col_offset,
                        message="Assert with tuple is always True",
                        suggested_fix="Remove the tuple: assert condition, message",
                        confidence=0.95,
                    ))
                self.generic_visit(node)

            def visit_Compare(self, node):
                """Check for suspicious comparisons."""
                # Check for 'is' comparison with literals
                for op, comparator in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.Is, ast.IsNot)):
                        if isinstance(comparator, ast.Constant):
                            if isinstance(comparator.value, (int, str, float)) and comparator.value not in (True, False, None):
                                issues.append(Issue(
                                    type=IssueType.SYNTAX_ISSUE,
                                    severity=Severity.WARNING,
                                    filepath=filepath,
                                    line=node.lineno,
                                    column=node.col_offset,
                                    message="Use == instead of 'is' for value comparison",
                                    suggested_fix="Replace 'is' with '=='",
                                    confidence=0.9,
                                ))
                self.generic_visit(node)

            def visit_Expr(self, node):
                """Check for statements with no effect."""
                # Check for comparison as statement (probably missing assignment)
                if isinstance(node.value, ast.Compare):
                    issues.append(Issue(
                        type=IssueType.SYNTAX_ISSUE,
                        severity=Severity.WARNING,
                        filepath=filepath,
                        line=node.lineno,
                        column=node.col_offset,
                        message="Comparison has no effect (result not used)",
                        suggested_fix="Assign the result or use in a condition",
                        confidence=0.8,
                    ))
                # Check for string literal as statement (except docstrings)
                elif isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    # This could be a docstring, so lower confidence
                    pass
                self.generic_visit(node)

        checker = ASTChecker()
        checker.visit(tree)

        return issues
