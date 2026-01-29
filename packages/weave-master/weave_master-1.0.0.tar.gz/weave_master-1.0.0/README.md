# Code Weaver

A proactive code healer that predicts and fixes Python issues before they cause problems, with ML-based learning from user feedback.

## Features

- **AST-based Analysis**: Deep code analysis using Python's Abstract Syntax Tree
- **Issue Detection**: Finds undefined variables, unused imports, type errors, and syntax issues
- **Auto-fix Suggestions**: Intelligent fix suggestions with confidence scores
- **ML Learning**: Learns from your feedback to improve fix suggestions over time
- **File Watching**: Continuous monitoring with automatic issue detection
- **Safe Healing**: Rollback support and atomic file operations

## Installation

```bash
pip install code-weaver
```

## Quick Start

### Command Line

```bash
# Analyze a file or directory
weave check src/
weave check myfile.py

# Watch mode (continuous monitoring)
weave watch src/

# Interactive fix mode
weave heal src/myfile.py

# Rollback last fix
weave rollback src/myfile.py

# View/manage ML model
weave model status        # Show model stats
weave model retrain       # Force retrain
weave model reset         # Reset to baseline

# Configure
weave config set auto_heal true
weave config set confidence_threshold 0.85
```

### Python API

```python
from code_weaver import Weaver, analyze_file, analyze_code

# Quick analysis
issues = analyze_file("mycode.py")
issues = analyze_code("x = undefined_var")

# Full control
weaver = Weaver(
    auto_heal=False,
    confidence_threshold=0.8,
    learn=True,  # Enable ML feedback
)

# Analyze
issues = weaver.analyze("src/")

# Apply fixes interactively
for issue in issues:
    if issue.suggested_fix:
        weaver.apply_fix(issue)  # Prompts for confirmation

# Watch mode
weaver.watch("src/", callback=my_handler)
```

## Issue Types Detected

### Undefined Variables
- Detects use before assignment
- Suggests imports, typo fixes, or initialization

### Unused Imports
- Tracks all imports and their usage
- Safe removal suggestions

### Type Errors
- Detects obvious type mismatches (str + int, etc.)
- Uses type hints when available

### Syntax Issues
- Missing colons, unmatched brackets
- f-string errors
- Indentation problems

## Configuration

Code Weaver stores its configuration in `~/.config/code_weaver/config.json`:

```json
{
    "auto_heal": false,
    "confidence_threshold": 0.8,
    "watch_debounce_ms": 300,
    "max_history_per_file": 50,
    "ignore_patterns": [".git", "__pycache__", "venv", ".venv", "node_modules"]
}
```

## ML Feedback System

Code Weaver learns from your decisions:

1. When you accept or reject a fix, the feedback is recorded
2. Features are extracted from each issue (type, severity, context, etc.)
3. A RandomForest classifier learns your preferences
4. Future suggestions are ranked by predicted acceptance probability

Force retrain the model:
```bash
weave model retrain
```

Reset to baseline:
```bash
weave model reset
```

## License

MIT License - see LICENSE file for details.
