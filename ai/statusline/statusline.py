#!/usr/bin/env python3
"""Claude Code status line for macOS."""

import json
import os
import subprocess
import sys


ESC = "\x1b"
RESET = f"{ESC}[0m"
DIM = f"{ESC}[90m"
SEP = f"{DIM}│{RESET}"


def fg(red, green, blue):
    return f"{ESC}[38;2;{red};{green};{blue}m"


def nested(data, *keys, default=None):
    value = data
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    return default if value is None else value


def context_part(data):
    used = nested(data, "context_window", "used_percentage")
    if used is None:
        return f"{DIM}ctx n/a{RESET}"

    used = round(float(used))
    free = 100 - used
    width = 14
    fill = max(0, min(width, round(width * used / 100)))
    bar = []
    for index in range(width):
        if index >= fill:
            bar.append(f"{fg(60, 60, 60)}░")
            continue
        position = (index + 0.5) / width * 100
        if position <= 50:
            ratio = position / 50
            color = fg(int(220 * ratio), 200, int(80 - 80 * ratio))
        else:
            ratio = (position - 50) / 50
            color = fg(220, int(200 - 160 * ratio), int(20 * ratio))
        bar.append(f"{color}█")

    if used >= 90:
        icon = "🚨"
    elif used >= 70:
        icon = "🔥"
    elif used >= 20:
        icon = "⚡"
    else:
        icon = "🟢"
    return f"{icon} {''.join(bar)}{RESET} {DIM}{free:.0f}% free{RESET}"


def git_branch(data):
    directory = nested(data, "workspace", "current_dir") or data.get("cwd")
    if not directory:
        return ""
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    for command in (("branch", "--show-current"), ("rev-parse", "--short", "HEAD")):
        try:
            result = subprocess.run(
                ["git", "-C", str(directory), *command],
                text=True,
                capture_output=True,
                timeout=1,
                env=environment,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        value = result.stdout.strip()
        if result.returncode == 0 and value:
            return value
    return ""


def render(data):
    cost = float(nested(data, "cost", "total_cost_usd", default=0) or 0)
    cost_text = f"${cost:.3f}" if 0 < cost < 0.01 else f"${cost:.2f}"
    cost_part = f"{fg(220, 200, 0)}SESSION {cost_text}{RESET}"

    added = int(nested(data, "cost", "total_lines_added", default=0) or 0)
    removed = int(nested(data, "cost", "total_lines_removed", default=0) or 0)
    velocity = f"{fg(0, 200, 80)}+{added}{RESET} {fg(220, 40, 20)}-{removed}{RESET}"

    parts = [cost_part, context_part(data)]
    branch = git_branch(data)
    if branch:
        parts.append(f"{fg(190, 130, 255)}{branch}{RESET}")
    parts.append(velocity)
    return f" {SEP} ".join(parts)


def main():
    try:
        data = json.load(sys.stdin)
        if isinstance(data, dict):
            print(render(data))
    except (TypeError, ValueError, OSError):
        pass


if __name__ == "__main__":
    main()
