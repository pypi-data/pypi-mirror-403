"""Auto-fix generation for detected issues."""

import re
from pathlib import Path

from code_weaver.issues.base import Issue, IssueType


class Fixer:
    """Generates and applies fixes for detected issues."""

    def generate_fix(self, issue: Issue, source_code: str) -> str | None:
        """
        Generate a fixed version of the source code.

        Args:
            issue: The issue to fix
            source_code: Original source code

        Returns:
            Fixed source code, or None if fix cannot be generated
        """
        if issue.suggested_fix is None:
            return None

        lines = source_code.splitlines(keepends=True)

        # Ensure we have the line
        if issue.line < 1 or issue.line > len(lines):
            return None

        fix_method = self._get_fix_method(issue.type)
        if fix_method:
            return fix_method(issue, lines)

        return None

    def _get_fix_method(self, issue_type: IssueType):
        """Get the appropriate fix method for an issue type."""
        fix_methods = {
            IssueType.UNDEFINED_VAR: self._fix_undefined_var,
            IssueType.UNUSED_IMPORT: self._fix_unused_import,
            IssueType.TYPE_ERROR: self._fix_type_error,
            IssueType.SYNTAX_ISSUE: self._fix_syntax_issue,
        }
        return fix_methods.get(issue_type)

    def _fix_undefined_var(self, issue: Issue, lines: list[str]) -> str | None:
        """Fix undefined variable issues."""
        context = issue.context
        name = context.get("name")
        similar_names = context.get("similar_names", [])

        if not name:
            return None

        # If we have a suggested similar name, replace it
        if similar_names and issue.suggested_fix:
            suggested = issue.suggested_fix
            line_idx = issue.line - 1
            line = lines[line_idx]

            # Replace the undefined name with the suggested one
            # Use word boundaries to avoid partial replacements
            pattern = rf'\b{re.escape(name)}\b'
            new_line = re.sub(pattern, suggested, line)

            if new_line != line:
                lines[line_idx] = new_line
                return "".join(lines)

        return None

    def _fix_unused_import(self, issue: Issue, lines: list[str]) -> str | None:
        """Fix unused import issues."""
        context = issue.context
        line_content = context.get("line_content", "")
        name = context.get("name")
        is_from_import = context.get("is_from_import", False)

        if not name:
            return None

        line_idx = issue.line - 1
        line = lines[line_idx]

        # Check if this is a multi-import line
        if is_from_import:
            # from X import a, b, c
            if "," in line:
                # Try to remove just this import
                # Match patterns like "name," or ", name" or "name"
                patterns = [
                    rf'\b{re.escape(name)}\s*,\s*',  # name, ...
                    rf',\s*{re.escape(name)}\b',     # ..., name
                    rf'\b{re.escape(name)}\b',       # just name
                ]
                for pattern in patterns:
                    new_line = re.sub(pattern, '', line)
                    if new_line != line:
                        # Check if the import is now empty
                        if re.match(r'from\s+\S+\s+import\s*$', new_line.strip()):
                            # Remove the entire line
                            lines[line_idx] = ""
                        else:
                            lines[line_idx] = new_line
                        return "".join(lines)
            else:
                # Single import - remove the line
                lines[line_idx] = ""
                return "".join(lines)
        else:
            # import X or import X, Y
            if "," in line:
                # Try to remove just this import
                patterns = [
                    rf'\b{re.escape(name)}\s*,\s*',
                    rf',\s*{re.escape(name)}\b',
                    rf'\b{re.escape(name)}\b',
                ]
                for pattern in patterns:
                    new_line = re.sub(pattern, '', line)
                    if new_line != line:
                        if re.match(r'import\s*$', new_line.strip()):
                            lines[line_idx] = ""
                        else:
                            lines[line_idx] = new_line
                        return "".join(lines)
            else:
                # Single import - remove the line
                lines[line_idx] = ""
                return "".join(lines)

        return None

    def _fix_type_error(self, issue: Issue, lines: list[str]) -> str | None:
        """Fix type error issues."""
        context = issue.context
        left_type = context.get("left_type")
        right_type = context.get("right_type")
        source = context.get("source")

        if not source:
            return None

        line_idx = issue.line - 1
        line = lines[line_idx]

        # Simple fix: wrap one side in str() or int()
        if left_type == "str" and right_type == "int":
            # Find the int and wrap in str()
            # This is a simple heuristic
            new_line = line.replace(source, source.replace("+", "+ str(") + ")")
            if new_line != line:
                lines[line_idx] = new_line
                return "".join(lines)

        return None

    def _fix_syntax_issue(self, issue: Issue, lines: list[str]) -> str | None:
        """Fix syntax issues."""
        message = issue.message.lower()

        line_idx = issue.line - 1
        line = lines[line_idx]

        # Missing colon
        if "missing colon" in message:
            if not line.rstrip().endswith(":"):
                lines[line_idx] = line.rstrip() + ":\n"
                return "".join(lines)

        # Python 2 print statement
        if "python 2 style print" in message:
            # Convert print x to print(x)
            match = re.match(r'^(\s*)print\s+(.+)$', line.rstrip())
            if match:
                indent = match.group(1)
                args = match.group(2)
                lines[line_idx] = f"{indent}print({args})\n"
                return "".join(lines)

        return None

    def generate_diff(self, issue: Issue, source_code: str) -> str | None:
        """
        Generate a unified diff showing the proposed fix.

        Args:
            issue: The issue to fix
            source_code: Original source code

        Returns:
            Unified diff string, or None if fix cannot be generated
        """
        fixed = self.generate_fix(issue, source_code)
        if fixed is None:
            return None

        import difflib

        original_lines = source_code.splitlines(keepends=True)
        fixed_lines = fixed.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f"a/{issue.filepath}",
            tofile=f"b/{issue.filepath}",
            lineterm="",
        )

        return "".join(diff)

    def apply_fix_to_file(self, issue: Issue, filepath: str | Path) -> bool:
        """
        Apply a fix directly to a file.

        Args:
            issue: The issue to fix
            filepath: Path to the file to modify

        Returns:
            True if fix was applied, False otherwise
        """
        filepath = Path(filepath)

        if not filepath.exists():
            return False

        source_code = filepath.read_text(encoding="utf-8")
        fixed = self.generate_fix(issue, source_code)

        if fixed is None:
            return False

        filepath.write_text(fixed, encoding="utf-8")
        return True
