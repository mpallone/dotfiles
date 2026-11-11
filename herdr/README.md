# herdr: one key opens a new Codex tab

Press `ctrl+s`, then `Shift+C`, inside herdr to open a new tab running Codex.
[herdr](https://herdr.dev) is a terminal workspace manager for AI coding
agents, similar to tmux; Codex is OpenAI's command-line coding agent. The key
needs no macOS permissions, driver, or helper app, so it works the same on
macOS and Linux.

To set this up on a new machine, give an agent
[INSTALL_PROMPT.md](INSTALL_PROMPT.md). It covers installing herdr and Codex.

## How the key reaches Codex

```text
ctrl+s, Shift+C ─► herdr custom command key ─► ~/.local/bin/herdr-codex-tab
 (prefix+shift+c)   ([[keys.command]] in         ├─► herdr tab create --label Codex --focus
                     config.toml)                └─► herdr pane run <new pane> codex
```

`prefix+c` is herdr's built-in "new tab"; adding Shift makes it a Codex tab.
The launcher types `codex` into the new pane's interactive shell, so a `codex`
alias or function applies as it does when typed by hand. The tab is created in
the session and workspace where the key was pressed.

Example: with one tab open, two presses leave three tabs, `1`, `Codex`, and
`Codex`, and `herdr agent list` reports two `codex` agents.

## Install on a machine that already has herdr, Codex, and jq

```sh
bash herdr/install.sh
```

| File | Deployed to | How |
|---|---|---|
| `codex-tab.sh` | `~/.local/bin/herdr-codex-tab` | symlink |
| `config.toml` | `~/.config/herdr/config.toml` | copy, or append to an existing file |

`config.toml` is copied because herdr writes to that file itself; dismissing
the first-run screen adds `onboarding = false`. An existing config is never
replaced: the installer backs it up and appends only the marked
`[[keys.command]]` block. It leaves an existing `[keys]` table alone, so set
`prefix = "ctrl+s"` there by hand if the machine should match this repo.
Running herdr sessions are reloaded; no restart is needed.

## Prove the key works without a keyboard

```sh
bash herdr/test-codex-key.sh
# PASS: C-s then C opened tab w1:t2 "Codex"; herdr detected codex in w1:p2
```

The test starts a throwaway herdr session inside tmux, types the key chord
into that real herdr client, and polls the herdr CLI until a tab labelled
`Codex` hosts a detected Codex agent. It uses a temporary copy of the installed
config with the first-run screen turned off, leaves the default session
untouched, and removes the throwaway session on exit. An unbound chord fails:
`CHORD_KEY=y bash herdr/test-codex-key.sh` exits 1 after 45 seconds.

## What was verified, and what was not

Verified on 2026-11-11 on Linux x86_64 (Ubuntu 24.04) with herdr 0.9.5,
codex-cli 0.167.1, tmux 3.4, and `/bin/sh` as dash:

- The key opens a Codex tab with the default `ctrl+b` prefix and with this
  repo's `ctrl+s` prefix.
- Two presses open two Codex tabs, the second pressed from inside a Codex pane.
- Installing into a running, attached session takes effect after the
  installer's config reload, with no restart.
- A fresh install, an append to an existing config, and a repeat install.
- Failures print to stderr and append to `~/.config/herdr/codex-tab.log`.

Not verified, because the test machine was a Linux container with no Codex
sign-in:

- macOS, iTerm, and `/bin/sh` as bash. The launcher uses only POSIX `sh`.
- The macOS failure notification, which calls `osascript`.
- Pressing the key while a signed-in Codex prompt has focus. Codex ran only as
  far as its sign-in screen. Herdr handles the prefix before the pane sees it.
- herdr versions other than 0.9.5.

Run `bash herdr/test-codex-key.sh` on each new machine to close these gaps.

## This key and the butterfly key are separate routes

| | This key | [Butterfly key](../hotkeys/README.md) |
|---|---|---|
| Works from | inside herdr | any macOS app |
| Platforms | macOS, Linux | macOS with iTerm |
| Needs | herdr config only | compiled helper app, login agent, F18 firmware mapping, Automation permission |
| Launcher | `herdr/codex-tab.sh` | `shortcuts/new-codex-session.sh` |

Use both: the butterfly key from another app, this key when herdr already
has focus or on a machine where the helper app cannot be installed.

The two launchers repeat about 15 lines of "create tab, run codex, wait for
detection". They were kept apart so this change does not edit the macOS
launcher, which could not be re-tested from Linux. The cost is that a change to
launch behavior must be made in both files.

## When the key does nothing

- **First run of herdr on the machine.** The first-run screen and the settings
  screen that follows it swallow key chords. Dismiss both, then press again.
- **Check the binding is loaded.** Press the prefix, then `?`, and filter for
  `new Codex tab`. If it is missing, run `herdr server reload-config`.
- **Run the launcher by hand** from a shell inside a herdr pane:
  `~/.local/bin/herdr-codex-tab`. It prints the reason on failure.
- **Read the log.** Key presses run detached, so their errors go to
  `~/.config/herdr/codex-tab.log`. Herdr toasts are off by default; set
  `[ui.toast] delivery = "herdr"` to see failures in the app.
- **`codex: command not found` in the new tab.** The pane's shell cannot find
  Codex. Fix the shell `PATH`; the key itself worked.
