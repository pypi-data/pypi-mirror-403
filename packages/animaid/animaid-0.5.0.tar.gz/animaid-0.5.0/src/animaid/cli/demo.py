#!/usr/bin/env python3
"""CLI entry point for running AnimAID demos.

Usage:
    animaid-demo [name]
    animaid-demo --list
"""

import argparse
import subprocess
import sys
from pathlib import Path

AVAILABLE_DEMOS = {
    "countdown_timer": "Real-time countdown with color transitions",
    "live_list": "Reactive shopping cart list",
    "score_tracker": "Game score tracking with dict updates",
    "sorting_visualizer": "Bubble sort algorithm visualization",
    "dashboard": "Multi-type dashboard with all HTML types",
    "typewriter": "Typewriter effect with styling animation",
    "todo_app": "Interactive todo list mini app",
    "data_pipeline": "ETL pipeline progress tracking",
    "input_greeter": "Interactive greeter with text input and button",
    "input_counter": "Counter with increment/decrement buttons",
    "input_slider": "RGB color mixer with sliders",
    "input_form": "Registration form with multiple input types",
    "input_button": "Button styles, sizes, and click event handling",
    "input_text": "Text input with live typing feedback and validation",
    "input_checkbox": "Checkbox toggles and multi-checkbox patterns",
    "input_select": "Select dropdowns with dynamic updates",
    "container_layout": "HTMLRow and HTMLColumn container layouts",
    "container_card": "HTMLCard with shadows, borders, and presets",
    "container_divider": "HTMLDivider for visual content separation",
    "container_spacer": "HTMLSpacer for fixed and flexible spacing",
    "container_row_column": "Flexbox layouts with alignment options",
}


def find_demos_dir() -> Path | None:
    """Find the demos directory."""
    # Try relative to this file (for installed package)
    pkg_root = Path(__file__).parent.parent.parent.parent
    demos_dir = pkg_root / "demos"
    if demos_dir.exists():
        return demos_dir

    # Try current working directory
    cwd_demos = Path.cwd() / "demos"
    if cwd_demos.exists():
        return cwd_demos

    return None


def list_demos() -> None:
    """List all available demos."""
    print("Available AnimAID demos:")
    print()
    for name, description in AVAILABLE_DEMOS.items():
        print(f"  {name:20} - {description}")
    print()
    print("Run a demo with: animaid-demo <name>")
    print("Example: animaid-demo countdown_timer")


def run_demo(name: str) -> int:
    """Run a specific demo."""
    if name not in AVAILABLE_DEMOS:
        print(f"Unknown demo: {name}")
        print()
        list_demos()
        return 1

    demos_dir = find_demos_dir()
    if demos_dir is None:
        print("Error: Could not find demos directory.")
        print("Make sure you're running from the animaid repository,")
        print("or install animaid from source.")
        return 1

    demo_file = demos_dir / f"{name}.py"
    if not demo_file.exists():
        print(f"Error: Demo file not found: {demo_file}")
        return 1

    print(f"Running demo: {name}")
    print(f"Description: {AVAILABLE_DEMOS[name]}")
    print("-" * 50)

    try:
        result = subprocess.run([sys.executable, str(demo_file)])
        return result.returncode
    except KeyboardInterrupt:
        print("\nDemo stopped.")
        return 0


def main() -> int:
    """Run an AnimAID demo program."""
    parser = argparse.ArgumentParser(
        description="Run AnimAID demo programs",
        prog="animaid-demo",
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="Name of the demo to run",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all available demos",
    )

    args = parser.parse_args()

    if args.list or args.name is None:
        list_demos()
        return 0

    return run_demo(args.name)


if __name__ == "__main__":
    sys.exit(main())
