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
- This may be a managed work laptop. If an install is blocked by policy, a
  proxy, or missing admin rights, stop and report it; do not work around it.

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
`git -C "$repo" pull --ff-only`. If it has uncommitted changes or is on
another branch, leave it untouched, clone a second copy to a new directory
under `/tmp`, and use that copy as `$repo` for the remaining steps.

Confirm `ls "$repo/herdr/install.sh"` succeeds. Run the remaining commands
from `$repo`.

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

If that prints a version, skip to step 5. Otherwise use the first route that
works:

1. Homebrew is installed (`command -v brew`):

   ```sh
   brew install herdr
   ```

2. The official installer, which verifies a SHA-256 checksum and installs to
   `~/.local/bin`:

   ```sh
   curl -fsSL https://herdr.dev/install.sh | sh
   ```

3. If `herdr.dev` is unreachable, download the release binary from GitHub and
   check it against herdr's published manifest. This route was verified on
   2026-11-11:

   ```sh
   case "$(uname -s)" in Darwin) os=macos ;; *) os=linux ;; esac
   case "$(uname -m)" in arm64 | aarch64) arch=aarch64 ;; *) arch=x86_64 ;; esac
   manifest="$(curl -fsSL https://raw.githubusercontent.com/herdrdev/herdr/master/distribution/latest.json)"
   url="$(printf '%s' "$manifest" | jq -er --arg t "$os-$arch" '.assets[$t]')"
   want="$(printf '%s' "$manifest" | jq -er --arg t "$os-$arch" '.sha256[$t]')"
   tmp="$(mktemp -d)"
   curl -fsSL -o "$tmp/herdr" "$url"
   got="$( (sha256sum "$tmp/herdr" 2>/dev/null || shasum -a 256 "$tmp/herdr") | awk '{print $1}')"
   if [ "$got" = "$want" ]; then
     mkdir -p "$HOME/.local/bin" && install -m 755 "$tmp/herdr" "$HOME/.local/bin/herdr"
   else
     echo "CHECKSUM MISMATCH: got $got, want $want. Not installed."
   fi
   ```

   On a checksum mismatch, stop and report it.

Check: `herdr --version` prints `herdr 0.9.5` or later. If the command is not
found but `~/.local/bin/herdr --version` works, `~/.local/bin` is missing from
`PATH`: tell the user which line to add to their shell startup file, and run
`export PATH="$HOME/.local/bin:$PATH"` for the remaining steps.

## 5. Install Codex if it is missing

```sh
codex --version
```

The launcher types `codex` into an interactive shell, so a `codex` alias or
function also counts. Check that case with `"$SHELL" -ic 'type codex'`.

If Codex is missing on a work laptop, ask the user before installing; the
company may require a specific distribution or provider configuration.
Otherwise run `npm install -g @openai/codex` (verified on 2026-11-11). Without
Node.js, OpenAI documents `brew install --cask codex`; this repository has not
exercised that route.

## 6. Install the key

```sh
bash herdr/install.sh
```

Expected: one `[ok]   linked ...herdr-codex-tab...` line, then either
`[ok]   copied config ...`, `[ok]   appended the Codex tab key ...`, or
`[skip] ... already has the Codex tab key`. A `[warn]` line names a tool from
steps 3 to 5 that is still missing; fix it and rerun.

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

Expected, within about 15 seconds:

```text
PASS: C-s then C opened tab w1:t2 "Codex"; herdr detected codex in w1:p2
```

If the machine's herdr prefix is not `ctrl+s`, pass it in tmux key notation,
for example `PREFIX_KEY=C-b bash herdr/test-codex-key.sh` for `ctrl+b`.

The test types the key chord into a real herdr client attached to a throwaway
session, then removes that session. It does not touch the user's default herdr
session. On `FAIL`, the output includes the herdr screen; also read
`~/.config/herdr/codex-tab.log` and the "When the key does nothing" section
of [README.md](README.md). If tmux cannot be installed, say so in the report
and ask the user to press the key by hand; do not report the key as verified.

## 8. macOS with the Keyboardio butterfly key only: the global key

Skip this step unless the user asks for it. It adds a second route, a macOS
Quick Action bound to F18, that works while another app has focus. It needs
iTerm, and it was not tested by the change that added this file.

```sh
bash quick-actions/install.sh
```

Then report these user-only steps from
[quick-actions/README.md](../quick-actions/README.md): set the butterfly key to
raw key code 109 (F18) in Chrysalis, choose **Finder → Services → Launch Codex
Session** once, and approve the macOS prompt that lets it control iTerm.

## 9. Report to the user

Lead with whether the test printed `PASS`. Then list:

- `uname -sm`, and the herdr, Codex, jq, and tmux versions.
- What you installed and by which route, and what was already present.
- The exact output of `bash herdr/install.sh` and `bash herdr/test-codex-key.sh`.
- The key to press, using the machine's actual herdr prefix.
- Steps left for the user: start `herdr`, dismiss its first-run screen (it
  swallows key chords until dismissed), sign in to Codex on first launch, and
  any `PATH` line or prefix change noted above.
