"""Command-line interface for Code Weaver."""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from code_weaver.core.detector import Detector
from code_weaver.core.fixer import Fixer
from code_weaver.healing.applier import FixApplier
from code_weaver.healing.history import HistoryManager
from code_weaver.issues.base import Issue, Severity
from code_weaver.ml.feedback import FeedbackStore
from code_weaver.ml.model import FixPredictor
from code_weaver.watcher.monitor import FileWatcher

console = Console()

# Configuration defaults
DEFAULT_CONFIG = {
    "auto_heal": False,
    "confidence_threshold": 0.85,
    "watch_debounce_ms": 300,
    "max_history_per_file": 50,
    "ignore_patterns": [".git", "__pycache__", "venv", ".venv", "node_modules"],
}


def get_config_path() -> Path:
    """Get the path to the config file."""
    config_dir = Path.home() / ".config" / "code_weaver"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> dict:
    """Load configuration from file."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path) as f:
                user_config = json.load(f)
                return {**DEFAULT_CONFIG, **user_config}
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Save configuration to file."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def format_issue(issue: Issue, show_fix: bool = True) -> str:
    """Format an issue for display."""
    severity_colors = {
        Severity.ERROR: "red",
        Severity.WARNING: "yellow",
        Severity.HINT: "blue",
    }
    color = severity_colors.get(issue.severity, "white")

    location = f"{issue.filepath}:{issue.line}:{issue.column}"
    message = f"[{color}]{issue.severity.value.upper()}[/{color}] {issue.message}"

    result = f"  {location}\n    {message}"

    if show_fix and issue.suggested_fix:
        result += f"\n    [green]Fix:[/green] {issue.suggested_fix}"

    if issue.confidence < 1.0:
        result += f" [dim](confidence: {issue.confidence:.0%})[/dim]"

    return result


@click.group()
@click.version_option(version="1.0.0", prog_name="weave")
def main():
    """Code Weaver - A proactive code healer for Python."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--no-fix", is_flag=True, help="Don't show fix suggestions")
def check(path: str, output_json: bool, no_fix: bool):
    """Analyze Python files for issues."""
    path = Path(path)
    detector = Detector()

    if path.is_file():
        issues = detector.analyze_file(path)
        all_issues = {str(path): issues} if issues else {}
    else:
        all_issues = detector.analyze_directory(path)

    if output_json:
        output = {
            filepath: [issue.to_dict() for issue in issues]
            for filepath, issues in all_issues.items()
        }
        console.print_json(json.dumps(output, indent=2))
        return

    if not all_issues:
        console.print("[green]✓[/green] No issues found!")
        return

    total_issues = sum(len(issues) for issues in all_issues.values())
    console.print(f"\n[bold]Found {total_issues} issue(s):[/bold]\n")

    for filepath, issues in all_issues.items():
        for issue in issues:
            console.print(format_issue(issue, show_fix=not no_fix))
            console.print()

    # Summary by severity
    errors = sum(1 for issues in all_issues.values() for i in issues if i.severity == Severity.ERROR)
    warnings = sum(1 for issues in all_issues.values() for i in issues if i.severity == Severity.WARNING)
    hints = sum(1 for issues in all_issues.values() for i in issues if i.severity == Severity.HINT)

    console.print(f"[red]{errors} errors[/red], [yellow]{warnings} warnings[/yellow], [blue]{hints} hints[/blue]")

    sys.exit(1 if errors > 0 else 0)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--auto", is_flag=True, help="Auto-apply high-confidence fixes")
@click.option("--dry-run", is_flag=True, help="Show what would be fixed without applying")
def heal(path: str, auto: bool, dry_run: bool):
    """Interactively fix issues in Python files."""
    path = Path(path)
    detector = Detector()
    applier = FixApplier()
    predictor = FixPredictor()
    feedback_store = FeedbackStore()
    config = load_config()

    if path.is_file():
        issues = detector.analyze_file(path)
    else:
        all_issues = detector.analyze_directory(path)
        issues = [issue for issues in all_issues.values() for issue in issues]

    if not issues:
        console.print("[green]✓[/green] No issues found!")
        return

    fixable_issues = [i for i in issues if i.suggested_fix]

    if not fixable_issues:
        console.print(f"Found {len(issues)} issue(s), but none have automatic fixes.")
        return

    console.print(f"\nFound [bold]{len(fixable_issues)}[/bold] fixable issue(s):\n")

    fixed_count = 0
    skipped_count = 0

    for issue in fixable_issues:
        # Show the issue
        console.print(format_issue(issue))

        # Show diff preview
        diff = applier.preview_fix(issue)
        if diff:
            console.print()
            syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
            console.print(Panel(syntax, title="Proposed Fix", border_style="green"))

        if dry_run:
            console.print("[dim]Dry run - not applying[/dim]\n")
            continue

        # Decide whether to apply
        if auto:
            decision, confidence = predictor.predict(issue)
            if decision == "yes" and confidence >= config["confidence_threshold"]:
                if applier.apply_fix(issue):
                    console.print("[green]✓ Applied automatically[/green]\n")
                    feedback_store.record_feedback(issue, accepted=True)
                    fixed_count += 1
                else:
                    console.print("[red]✗ Failed to apply[/red]\n")
                continue

        # Interactive prompt
        choice = click.prompt(
            "Apply this fix?",
            type=click.Choice(["y", "n", "s"], case_sensitive=False),
            default="y",
            show_choices=True,
        )

        if choice.lower() == "y":
            if applier.apply_fix(issue):
                console.print("[green]✓ Applied[/green]\n")
                feedback_store.record_feedback(issue, accepted=True)
                fixed_count += 1
            else:
                console.print("[red]✗ Failed to apply[/red]\n")
        elif choice.lower() == "s":
            console.print("[dim]Skipped[/dim]\n")
            skipped_count += 1
        else:
            console.print("[dim]Rejected[/dim]\n")
            feedback_store.record_feedback(issue, accepted=False)
            skipped_count += 1

    # Maybe retrain the model
    predictor.maybe_retrain()

    console.print(f"\n[bold]Summary:[/bold] {fixed_count} fixed, {skipped_count} skipped")


@main.command()
@click.argument("path", type=click.Path(exists=True))
def watch(path: str):
    """Watch directory and report issues on file changes."""
    path = Path(path)
    config = load_config()

    def on_issues_detected(filepath: str, issues: list[Issue]):
        console.print(f"\n[bold]Issues in {filepath}:[/bold]")
        for issue in issues:
            console.print(format_issue(issue))

    console.print(f"[bold]Watching {path}...[/bold] (Press Ctrl+C to stop)\n")

    watcher = FileWatcher(
        callback=on_issues_detected,
        debounce_ms=config["watch_debounce_ms"],
        ignore_patterns=config["ignore_patterns"],
    )

    try:
        watcher.start(path)
        watcher.wait()
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching[/dim]")
    finally:
        watcher.stop()


@main.command()
@click.argument("path", type=click.Path(exists=True))
def rollback(path: str):
    """Rollback the last fix applied to a file."""
    path = Path(path)
    history = HistoryManager()
    applier = FixApplier(history_manager=history)

    # Get rollback info
    info = applier.get_rollback_info(path)

    if info is None:
        console.print(f"[yellow]No history available for {path}[/yellow]")
        return

    console.print(f"[bold]Last fix:[/bold]")
    console.print(f"  Type: {info['issue_type']}")
    console.print(f"  Message: {info['issue_message']}")
    console.print(f"  Applied: {info['timestamp']}")

    if click.confirm("Rollback to previous state?"):
        if applier.rollback(path):
            console.print("[green]✓ Rolled back successfully[/green]")
        else:
            console.print("[red]✗ Rollback failed[/red]")


@main.group()
def model():
    """Manage the ML model."""
    pass


@model.command("status")
def model_status():
    """Show model status and statistics."""
    predictor = FixPredictor()
    status = predictor.get_status()

    table = Table(title="Model Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Trained", "Yes" if status["trained"] else "No")
    table.add_row("Feedback Count", str(status["feedback_count"]))
    table.add_row("Acceptance Rate", f"{status['acceptance_rate']:.1%}")
    table.add_row("Needs Retraining", "Yes" if status["needs_retraining"] else "No")
    table.add_row("Model Path", status["model_path"])

    console.print(table)

    if status["feedback_by_type"]:
        console.print("\n[bold]Feedback by Issue Type:[/bold]")
        for issue_type, counts in status["feedback_by_type"].items():
            accepted = counts.get("accepted", 0)
            rejected = counts.get("rejected", 0)
            total = accepted + rejected
            rate = accepted / total if total > 0 else 0
            console.print(f"  {issue_type}: {accepted}/{total} accepted ({rate:.0%})")


@model.command("retrain")
def model_retrain():
    """Force retrain the model."""
    predictor = FixPredictor()
    result = predictor.train(force=True)

    if result["status"] == "trained":
        console.print("[green]✓ Model trained successfully[/green]")
        console.print(f"  Samples: {result['samples']}")
        console.print(f"  Positive: {result['positive']}, Negative: {result['negative']}")
        if result.get("cv_score"):
            console.print(f"  Cross-validation score: {result['cv_score']:.2%}")
    elif result["status"] == "insufficient_data":
        console.print(f"[yellow]Not enough data ({result['samples']}/{result['required']} samples)[/yellow]")
    elif result["status"] == "no_data":
        console.print("[yellow]No feedback data available[/yellow]")
    elif result["status"] == "imbalanced":
        console.print("[yellow]Data too imbalanced to train[/yellow]")


@model.command("reset")
def model_reset():
    """Reset model to untrained state."""
    if click.confirm("This will delete the trained model. Continue?"):
        predictor = FixPredictor()
        predictor.reset()
        console.print("[green]✓ Model reset[/green]")


@main.group()
def config():
    """Manage configuration."""
    pass


@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = load_config()

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in cfg.items():
        table.add_row(key, str(value))

    console.print(table)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value."""
    cfg = load_config()

    if key not in DEFAULT_CONFIG:
        console.print(f"[red]Unknown configuration key: {key}[/red]")
        console.print(f"Valid keys: {', '.join(DEFAULT_CONFIG.keys())}")
        return

    # Parse value based on default type
    default_value = DEFAULT_CONFIG[key]
    if isinstance(default_value, bool):
        cfg[key] = value.lower() in ("true", "1", "yes")
    elif isinstance(default_value, int):
        cfg[key] = int(value)
    elif isinstance(default_value, float):
        cfg[key] = float(value)
    elif isinstance(default_value, list):
        cfg[key] = value.split(",")
    else:
        cfg[key] = value

    save_config(cfg)
    console.print(f"[green]✓ Set {key} = {cfg[key]}[/green]")


@config.command("reset")
def config_reset():
    """Reset configuration to defaults."""
    if click.confirm("Reset all configuration to defaults?"):
        save_config(DEFAULT_CONFIG)
        console.print("[green]✓ Configuration reset[/green]")


if __name__ == "__main__":
    main()
