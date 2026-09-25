# karabiner

Keyboardio Model 100 butterfly key → new Codex tab inside herdr.

Pressing the butterfly key creates and selects a new tab inside herdr's default
session, then starts a fresh `codex` session. The launcher brings herdr's existing
iTerm tab forward. It opens an iTerm tab only when no default herdr client is
running in iTerm. The keyboard sends **F18**; Karabiner-Elements catches F18 and
runs a shell script that drives iTerm via AppleScript and herdr via its CLI.
Holding either Shift key with the butterfly key maps **Shift-F18** to a new
Safari tab.

The Any key can send **F19**, which Karabiner maps to a new plain iTerm tab.
Holding either Shift key with Any maps **Shift-F19** to a new Google Chrome tab.

## How it works

```
butterfly key  ──►  F18  ──►  Karabiner rule  ──►  codex-tab.sh
 (Chrysalis,        (HID      (complex_                  ├──► select herdr's iTerm tab
  raw code 109)     0x6D)      modification)             └──► new herdr tab + `codex`

Shift + butterfly ──► Shift-F18 ──► Karabiner rule ──► safari-tab.sh ──► new Safari tab

Any key        ──►  F19  ──►  Karabiner rule  ──►  terminal-tab.sh  ──►  plain iTerm tab
 (raw code 110)

Shift + Any    ──►  Shift-F19  ──►  Karabiner rule  ──►  chrome-tab.sh  ──►  new Chrome tab
```

F18 and F19 are used because macOS binds nothing to them by default.

The new herdr tab uses the active workspace and herdr's configured directory
policy. If no workspace exists, the launcher creates one. It runs `codex` in the
pane's interactive shell so shell aliases still apply. For example, two presses
create two Codex tabs within the same herdr overview, without adding iTerm tabs.
Named herdr sessions are left alone. Closing the iTerm tab detaches the client;
the Codex terminals continue running in herdr's background server.

The launcher requires `herdr` on `PATH` or in `~/.local/bin`. It uses macOS's
built-in `jq` and `shlock`, serializes overlapping presses, and reports startup
failures through stderr and a macOS notification.

## Files

| File | Deployed to | How |
|---|---|---|
| `scripts/codex-tab.sh` | `~/.config/karabiner/scripts/` | symlink |
| `scripts/safari-tab.sh` | `~/.config/karabiner/scripts/` | symlink |
| `scripts/terminal-tab.sh` | `~/.config/karabiner/scripts/` | symlink |
| `scripts/chrome-tab.sh` | `~/.config/karabiner/scripts/` | symlink |
| `assets/complex_modifications/butterfly-claude.json` | `~/.config/karabiner/assets/complex_modifications/` | symlink |
| `assets/complex_modifications/shift-f18-safari-tab.json` | `~/.config/karabiner/assets/complex_modifications/` | symlink |
| `assets/complex_modifications/f19-terminal-tab.json` | `~/.config/karabiner/assets/complex_modifications/` | symlink |
| `assets/complex_modifications/shift-f19-chrome-tab.json` | `~/.config/karabiner/assets/complex_modifications/` | symlink |
| `karabiner.json` | `~/.config/karabiner/` | **copy** |

`karabiner.json` is copied rather than symlinked because Karabiner rewrites
that file itself and replaces a symlink with a regular file. Verified on
2026-09-07 with Karabiner 16.3.0. Karabiner only reads the linked files, so
their symlinks hold and repo edits are live immediately.

**After changing Karabiner settings in the GUI, re-snapshot the config:**

```sh
cp ~/.config/karabiner/karabiner.json ~/src/mpallone/dotfiles/karabiner/karabiner.json
```

Otherwise this repo drifts from what is actually running.

## Restoring on a new machine

Install iTerm2 and Codex first, then install herdr using its
[installation guide](https://herdr.dev/docs/install/). Verify both commands
are available in a fresh iTerm shell:

```sh
herdr --version
codex --version
```

This launcher was verified with herdr 0.9.1. It uses the default herdr session
and needs no custom herdr configuration. Do not copy this laptop's herdr
runtime files or saved terminal state to the new laptop.

Run `bash karabiner/install.sh` from this repo to link the launcher into
`~/.config/karabiner/scripts/`, then complete the setup steps below. The installer
uses its own location, so this repo can live at a different path on the new laptop.

### 1. Install Karabiner-Elements

```sh
brew install --cask karabiner-elements
```

Run this in a **real terminal**. The cask installs a `.pkg` via `sudo`, and
macOS uses per-terminal sudo tickets — a non-TTY shell fails with
`sudo: a terminal is required to read the password`.

### 2. Approve the driver extension

Launch Karabiner-Elements once. It requests a DriverKit virtual HID driver that
macOS blocks by default.

**System Settings → General → Login Items & Extensions → Driver Extensions →**
enable **Karabiner-DriverKit-VirtualHIDDevice**.

Verify:

```sh
systemextensionsctl list | grep pqrs
# want: [activated enabled]   (not "[activated waiting for user]")
```

### 3. Grant Input Monitoring + Accessibility

**System Settings → Privacy & Security → Input Monitoring** (and
**→ Accessibility**). Enable every Karabiner entry listed.

Without these, Karabiner never grabs the keyboard and `karabiner.json` is never
even created. The symptom is in the log:

```sh
tail /var/log/karabiner/core_service.log
# bad:  device_grabber is not started because the required permissions are not granted.
# good: Model 100 (device_id:...) hid device events monitor is started (grabbed).
```

`grabbed` is what you want — it means Karabiner is modifying that device's events.

### 4. Install the config

```sh
bash karabiner/install.sh
```

Karabiner picks up changes automatically; watch for `Load .../karabiner.json`
in `/var/log/karabiner/core_service.log`.

### 5. Set the keys in Chrysalis

**This is the dependency that lives outside this repo — it is stored on the
keyboard's own firmware, not on the Mac.**

In [Chrysalis](https://github.com/keyboardio/Chrysalis), set the butterfly key
on **Layer 0** to **raw key code 109** (HID `0x6D` = F18), then flash the
keyboard. Set the Any key to **raw key code 110** (HID `0x6E` = F19).
Karabiner cannot apply these firmware settings. If they are not set, Karabiner
sees the keys' default keycodes and the rules never fire.

No separate Chrysalis mapping is needed for Shift-butterfly or Shift-Any. The
keyboard sends the existing function-key code together with the Shift modifier.

### 6. Accept the Automation prompt

Press the butterfly key. macOS prompts *"Karabiner-Console-User-Server wants to
control iTerm."* Click **OK**. This grants
**System Settings → Privacy & Security → Automation**. The first press only
produces the prompt; press again afterward.

## Troubleshooting

**Butterfly does nothing.** Open **Karabiner-EventViewer** and press it. Expect
`key_code: f18`. If you see `right_option` or anything else, Chrysalis did not
save — redo step 5.

**Any does nothing.** Open **Karabiner-EventViewer** and press it. Expect
`key_code: f19`. A different code means Chrysalis did not save raw key code
110.

**F18 arrives but no tab opens.** Run the script directly:

```sh
~/.config/karabiner/scripts/codex-tab.sh
```

If a herdr tab opens this way but the key does not, check the Automation
permission (step 6). If `codex: command not found` appears in the new herdr tab,
its shell PATH lacks `~/.local/bin` — that is a shell-config problem, not a
Karabiner one. Run `herdr --session default status` to check the server and
`herdr --session default agent list` to check whether it detected Codex.

**Shift-F18 arrives but no Safari tab opens.** Run the script directly:

```sh
~/.config/karabiner/scripts/safari-tab.sh
```

The first run can trigger a macOS Automation prompt allowing Karabiner to
control Safari. Approve it, then try Shift-butterfly again.

**F19 arrives but no tab opens.** Run the script directly:

```sh
~/.config/karabiner/scripts/terminal-tab.sh
```

**Shift-F19 arrives but no Chrome tab opens.** Run the script directly:

```sh
~/.config/karabiner/scripts/chrome-tab.sh
```

The first run can trigger a macOS Automation prompt allowing Karabiner to
control Google Chrome. Approve it, then try Shift-Any again.

**Validate the rule** with Karabiner's own linter:

```sh
"/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli" \
  --lint-complex-modifications ~/.config/karabiner/assets/complex_modifications/butterfly-claude.json \
  ~/.config/karabiner/assets/complex_modifications/shift-f18-safari-tab.json \
  ~/.config/karabiner/assets/complex_modifications/f19-terminal-tab.json \
  ~/.config/karabiner/assets/complex_modifications/shift-f19-chrome-tab.json
# want: ok
```

## Changing what the key does

Edit the corresponding file under `scripts/` — each is symlinked, so the
change is live on the next press. No reload or reinstall is needed.
