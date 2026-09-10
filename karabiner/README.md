# karabiner

Keyboardio Model 100 butterfly key → new iTerm tab running `claude`.

Pressing the butterfly key opens a new tab in iTerm2 and starts a `claude`
session in it. The keyboard sends **F18**; Karabiner-Elements catches F18 and
runs a shell script that drives iTerm via AppleScript.

The Any key can send **F19**, which Karabiner maps to a new plain iTerm tab.

## How it works

```
butterfly key  ──►  F18  ──►  Karabiner rule  ──►  claude-tab.sh  ──►  osascript  ──►  iTerm
 (Chrysalis,        (HID      (complex_             (this repo)                        new tab
  raw code 109)     0x6D)      modification)                                           + `claude`

Any key        ──►  F19  ──►  Karabiner rule  ──►  terminal-tab.sh  ──►  plain iTerm tab
 (raw code 110)
```

F18 and F19 are used because macOS binds nothing to them by default.

## Files

| File | Deployed to | How |
|---|---|---|
| `scripts/claude-tab.sh` | `~/.config/karabiner/scripts/` | symlink |
| `scripts/terminal-tab.sh` | `~/.config/karabiner/scripts/` | symlink |
| `assets/complex_modifications/butterfly-claude.json` | `~/.config/karabiner/assets/complex_modifications/` | symlink |
| `assets/complex_modifications/f19-terminal-tab.json` | `~/.config/karabiner/assets/complex_modifications/` | symlink |
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

Run `bash karabiner/install.sh` for the file placement, then do the manual
steps — none of them are scriptable, all of them are required.

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
~/.config/karabiner/scripts/claude-tab.sh
```

If a tab opens this way but the key does not, the Automation permission
(step 6) is missing. If `claude: command not found` appears in the new tab,
iTerm's shell PATH lacks `~/.local/bin` — that is a shell-config problem, not a
Karabiner one.

**F19 arrives but no tab opens.** Run the script directly:

```sh
~/.config/karabiner/scripts/terminal-tab.sh
```

**Validate the rule** with Karabiner's own linter:

```sh
"/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli" \
  --lint-complex-modifications ~/.config/karabiner/assets/complex_modifications/butterfly-claude.json \
  ~/.config/karabiner/assets/complex_modifications/f19-terminal-tab.json
# want: ok
```

## Changing what the key does

Edit the corresponding file under `scripts/` — both are symlinked, so the
change is live on the next press. No reload or reinstall is needed.
