# Butterfly and Fun+3 work systemwide

Codex Hotkey registers F18 and F3 with macOS's systemwide hotkey API. F18
runs the shared Codex launcher; F3 opens Mission Control. It starts at
login and has no Dock icon. The native Quick Action remains available as
a manual fallback for launching Codex.

```text
butterfly → F18 → Codex Hotkey → new Herdr tab running codex
Fun+3     → F3  → Codex Hotkey → Mission Control
```

The helper uses Carbon's `RegisterEventHotKey` API, which reserves these
two keys instead of monitoring keyboard input. It does not require a Karabiner
driver or an Accessibility grant for hotkey registration. macOS can still
ask **Codex Hotkey** for permission to control iTerm; allow that Automation
request so the shared launcher can bring its window forward.

## Install and verify the helper

Install iTerm, Herdr, Codex, and Apple's Command Line Tools first. From
this repository's root:

```sh
bash hotkeys/install.sh
```

The installer compiles `codex-hotkey.swift`, installs
`~/Applications/Codex Hotkey.app`, links the existing launcher, and loads
`~/Library/LaunchAgents/com.mpallone.codex-hotkey.plist`. Building requires
the Swift compiler from Command Line Tools; no package download is needed.

Keep the butterfly key on raw key code **109** (F18) in Chrysalis. Press it
with Chrome in front, then with iTerm in front. Each press should select a
fresh Codex tab in Herdr. Press Fun+3 to open Mission Control. A held key
runs its action only once until released; the two keys track releases
independently.

## Restore Fun+3 without changing the keyboard layout

The Model 100's Fun key temporarily selects its function layer. In the
stored keyboard map, layer 2 assigns raw key code **60** (F3) to the 3 key.
This matches [Keyboardio's default function layer](https://github.com/keyboardio/Kaleidoscope/blob/master/examples/Devices/Keyboardio/Model100/Model100.ino#L293).

Karabiner previously supplied a default
[F3 → Mission Control translation](https://github.com/pqrs-org/Karabiner-Elements/blob/main/src/share/core_configuration/details/profile.hpp#L105).
This helper restores that translation by opening macOS's built-in
`/System/Applications/Mission Control.app` when F3 is pressed. The existing
Control+Up Mission Control shortcut remains available.

Bare F3 is reserved systemwide, so F3 from another keyboard also opens
Mission Control. No keyboard firmware change is needed. Verify Fun+3 with
Chrome in front, then verify butterfly still opens a fresh Codex tab.

The [Services Quick Action](../quick-actions/README.md) depends on the
front app handling its menu shortcut. Chrome and iTerm did not invoke F18
through that route on this Mac. This helper registers the key independently
of those menus, so those apps do not need to forward it.

## Check startup errors or uninstall

```sh
launchctl print "gui/$(id -u)/com.mpallone.codex-hotkey"
tail -n 30 ~/Library/Logs/CodexHotkey.log
```

The log should contain `registered systemwide F18 (Codex)` and
`registered systemwide F3 (Mission Control)`. Registration failures and
launcher errors are logged. A conflicting global key binding must be
removed from the other app before this helper can register it. If F3
registration fails, the helper keeps the Codex binding running.

To stop it and prevent startup at login:

```sh
launchctl bootout "gui/$(id -u)/com.mpallone.codex-hotkey"
rm ~/Library/LaunchAgents/com.mpallone.codex-hotkey.plist
```

The app bundle and launcher can remain installed. The Quick Action and
existing Herdr sessions are preserved.
