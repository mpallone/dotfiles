# Agent setup: one key opens a new Codex session in herdr

Give this file to a coding agent on the target machine, for example:

```text
Follow https://github.com/mpallone/dotfiles/blob/main/herdr/INSTALL_PROMPT.md
```

The rest of this file is addressed to that agent.

## Goal and definition of done

After setup, pressing `ctrl+s` and then `Shift+C` inside herdr opens a new tab
running Codex. [herdr](https://herdr.dev) is a terminal workspace manager for
AI coding agents, similar to tmux. Codex is OpenAI's command-line coding
agent. Setup is done when `bash herdr/test-codex-key.sh` prints `PASS`.

Supported: macOS and Linux. Last verified on 2026-11-11 on Linux x86_64 with
herdr 0.9.5 and codex-cli 0.167.1; macOS has not been verified, so the test in
step 7 is the proof on a Mac.

## Rules

- Run the steps in order. Run each check and compare its output to the
  expected output before continuing.
- If a step fails and this file gives no fix, stop and report the command, its
  full output, and what you tried. Do not improvise a different mechanism.
- Do not replace or reformat `~/.config/herdr/config.toml` or
  `~/.codex/config.toml`. Do not commit to or push the dotfiles repository.
- Never ask for, print, or store credentials. Signing in to Codex is the
  user's step.
- This may be a managed work laptop. Where a step lists several routes,
  moving to the next listed route is allowed. If every listed route is blocked
  by policy, a proxy, or missing admin rights, stop and report it; do not
  bypass the block.
- Commands assume one shell that keeps its directory and variables. If yours
  resets between commands, start each one with `cd "$repo"` and repeat any
  `export` this file asked for.
- Drop `sudo` from a command when you are already root.

## macOS shortcut for steps 3 to 8

On macOS, after step 2, one script does the work of steps 3 to 8:

```sh
bash herdr/setup-mac.sh
```

Add `--skip-butterfly` unless step 8 applies. Each line it prints starts with
`[ok]`, `[skip]`, `[warn]`, or `[fail]`, and it ends with the manual steps
left for the user. If it exits 0, go to step 9 and include its full output. If
it prints `[fail]`, use the matching numbered step below to diagnose. The
script has been simulated on Linux but not yet run on macOS, so read its
output with care. On Linux, follow the numbered steps.

## 1. Record the machine

```sh
uname -sm
echo "$SHELL"
```

Stop if the system is not `Darwin` or `Linux`.

## 2. Get the dotfiles repository

```sh
repo="$HOME/src/mpallone/dotfiles"
if [ -d "$repo/.git" ]; then
  git -C "$repo" status --short --branch
else
  mkdir -p "$(dirname "$repo")"
  git clone https://github.com/mpallone/dotfiles.git "$repo"
fi
```

If the checkout exists, is on `main`, and has no uncommitted changes, run
`git -C "$repo" pull --ff-only`. If it has uncommitted changes (untracked
files do not count), is on another branch, or the pull fails, leave it
untouched, clone a second copy to a new directory under `/tmp`, and use that
copy as `$repo` for the remaining steps.

Confirm `ls "$repo/herdr/install.sh"` succeeds. If it does not, the change
that added this file is not on `main` yet; stop and report that. Run the
remaining commands from `$repo`.

## 3. Install jq if it is missing

```sh
jq --version
```

macOS 15 and later ship `/usr/bin/jq`. Otherwise run `brew install jq`, or
`sudo apt-get install -y jq` on Debian or Ubuntu. The launcher, the test, and
step 4's fallback route all parse herdr's JSON output with jq.

## 4. Install herdr if it is missing

```sh
herdr --version
```

If that prints a version, skip to step 5. Otherwise try these routes in order
and move to the next when one is unavailable, fails, or is refused by your own
tooling:

1. Homebrew, when `command -v brew` succeeds:

   ```sh
   brew install herdr
   ```

2. The official installer, which verifies a SHA-256 checksum and installs to
   `~/.local/bin`. Check that the host is reachable first; a failed download
   piped into `sh` still exits 0.

   ```sh
   curl -fsSI https://herdr.dev/install.sh >/dev/null && curl -fsSL https://herdr.dev/install.sh | sh
   ```

3. The release binary from GitHub, checked against herdr's published
   manifest. This route was verified on 2026-11-11:

   ```sh
   case "$(uname -s)" in Darwin) os=macos ;; *) os=linux ;; esac
   case "$(uname -m)" in arm64 | aarch64) arch=aarch64 ;; *) arch=x86_64 ;; esac
   tmp="$(mktemp -d)"
   if curl -fsSL -o "$tmp/latest.json" https://raw.githubusercontent.com/herdrdev/herdr/master/distribution/latest.json &&
     url="$(jq -er --arg t "$os-$arch" '.assets[$t]' "$tmp/latest.json")" &&
     want="$(jq -er --arg t "$os-$arch" '.sha256[$t]' "$tmp/latest.json")" &&
     curl -fsSL -o "$tmp/herdr" "$url"; then
     got="$( (sha256sum "$tmp/herdr" 2>/dev/null || shasum -a 256 "$tmp/herdr") | awk '{print $1}')"
     if [ "$got" = "$want" ]; then
       mkdir -p "$HOME/.local/bin" && install -m 755 "$tmp/herdr" "$HOME/.local/bin/herdr" &&
         echo "INSTALLED herdr for $os-$arch, sha256 $got"
     else
       echo "CHECKSUM MISMATCH: got $got, want $want. Not installed."
     fi
   else
     echo "DOWNLOAD FAILED for $os-$arch. Not installed."
   fi
   rm -rf "$tmp"
   ```

   Expected: one `INSTALLED herdr ...` line. On `CHECKSUM MISMATCH` or
   `DOWNLOAD FAILED`, stop and report it.

Check: `herdr --version` prints `herdr 0.9.5` or later. If the command is not
found but `~/.local/bin/herdr --version` works, `~/.local/bin` is missing from
`PATH`: tell the user which line to add to their shell startup file, and run
`export PATH="$HOME/.local/bin:$PATH"` for the remaining steps.

## 5. Install Codex if it is missing

```sh
codex --version
```

If that prints a version, skip to step 6. If it fails, Codex may still exist
as a shell alias or function, which also works because the launcher types
`codex` into an interactive shell. Check with `"$SHELL" -ic 'type codex'`;
ignore `no job control` warnings in its output.

If Codex is missing, ask the user whether this is a work laptop before
installing; a company may require a specific distribution or provider
configuration. Otherwise run `npm install -g @openai/codex` (verified on 2026-11-11). Without
Node.js, OpenAI documents `brew install --cask codex`; this repository has not
exercised that route.

## 6. Install the key

```sh
bash herdr/install.sh
```

Expected: one `[ok]   linked ...herdr-codex-tab...` line, then either
`[ok]   copied config ...`, `[ok]   appended the Codex tab key ...`, or
`[skip] ... already has the Codex tab key`, then two closing lines that name
the key and the test. A `[warn]` line names a tool from steps 3 to 5 that is
still missing; fix it and rerun.

If the installer printed `[note] the existing [keys] table was left alone`,
read `~/.config/herdr/config.toml`. If its `[keys]` table has no `prefix`,
or a prefix other than `"ctrl+s"`, tell the user; do not change it yourself.
Use that machine's actual prefix in step 7 and in your report.

## 7. Prove the key works

The test needs tmux to hold a terminal for herdr. If `tmux -V` fails, install
it with `brew install tmux` or `sudo apt-get install -y tmux`.

```sh
bash herdr/test-codex-key.sh
```

Expected, within about 15 seconds. `PASS` shows that the key starts Codex; it
does not show that Codex is signed in:

```text
PASS: C-s then C opened tab w1:t2 "Codex"; herdr detected codex in w1:p2
```

If the machine's herdr prefix is not `ctrl+s`, pass it in tmux key notation,
for example `PREFIX_KEY=C-b bash herdr/test-codex-key.sh` for `ctrl+b`.

The test types the key chord into a real herdr client attached to a throwaway
session, then removes that session. It does not touch the user's default herdr
session. On `FAIL`, the output includes the herdr screen; also read
`~/.config/herdr/codex-tab.log`, which exists only once the launcher has
failed, and the "When the key does nothing" section of
[README.md](README.md). If tmux cannot be installed, say so in the report
and ask the user to press the key by hand; do not report the key as verified.

## 8. macOS with the Keyboardio butterfly key only: the systemwide key

This adds a second route: a helper app that registers F18, the key the
Keyboardio Model 100 butterfly key sends, so one press opens a Codex tab while
any app has focus. The same helper reserves F3 for Mission Control and F4 for
Spotlight on every keyboard attached to the Mac. Do it when the machine is a
Mac with iTerm and the user uses that keyboard; ask if you do not know. It was
not tested by the change that added this file, which ran on Linux.

It compiles a Swift program and installs a login agent, so it needs Apple's
Command Line Tools (`xcode-select -p` prints a path). On a managed laptop,
confirm with the user before installing a login agent.

```sh
bash hotkeys/install.sh
tail -n 30 ~/Library/Logs/CodexHotkey.log
```

Expected: the installer prints `Installed Codex Hotkey and enabled it at
login`, and the log contains `registered systemwide F18 (Codex)`. If the log
reports `could not register`, another app holds that key; report it.

You cannot press the key or approve macOS prompts. Report these user-only
steps from [hotkeys/README.md](../hotkeys/README.md): set the butterfly key to
raw key code 109 (F18) in Chrysalis, press it once, and allow **Codex Hotkey**
to control iTerm when macOS asks. For F4 to open Spotlight, enable **Codex
Hotkey** under Privacy & Security → Accessibility.

## 9. Report to the user

Lead with whether the test printed `PASS`. Then list:

- `uname -sm`, and the herdr, Codex, jq, and tmux versions.
- What you installed and by which route, and what was already present.
- The exact output of `bash herdr/install.sh` and `bash herdr/test-codex-key.sh`.
- The key to press, using the machine's actual herdr prefix.
- Steps left for the user: start `herdr`, dismiss its first-run screen (it
  swallows key chords until dismissed), sign in to Codex on first launch, and
  any `PATH` line or prefix change noted above.
