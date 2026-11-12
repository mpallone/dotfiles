# Butterfly and Fun-layer system actions

Codex Hotkey registers F18, F3, and F4 with macOS's systemwide hotkey API.
F18 runs the shared Codex launcher, F3 opens Mission Control, and F4 opens
Spotlight. It starts at
login and has no Dock icon. The native Quick Action remains available as
a manual fallback for launching Codex.

```text
butterfly → F18 → Codex Hotkey → new Herdr tab running codex
Fun+3     → F3  → Codex Hotkey → Mission Control
Fun+4     → F4  → Codex Hotkey → Spotlight
Fun+8     → native play/pause key → macOS media control
```

The helper uses Carbon's `RegisterEventHotKey` API, which reserves these
three keys instead of monitoring keyboard input. It does not require a Karabiner
driver or an Accessibility grant for hotkey registration. F4 invokes the
Spotlight shortcut configured in macOS, which requires **Codex Hotkey**
to be enabled in **Privacy & Security → Accessibility** for posting the
keyboard event. macOS can also
ask **Codex Hotkey** for permission to control iTerm; allow that Automation
request so the shared launcher can bring its window forward.

## Install and verify the helper

Install iTerm, Herdr, Codex, and Apple's Command Line Tools first. From
this repository's root:

```sh
bash hotkeys/install.sh
```

Restore the keyboard's native brightness/media actions using the
[Fun-layer setup](../keyboardio/README.md). Those settings are stored in
the keyboard and do not need to be reapplied on each Mac.

The installer compiles `codex-hotkey.swift`, installs
`~/Applications/Codex Hotkey.app`, links the existing launcher, and loads
`~/Library/LaunchAgents/com.mpallone.codex-hotkey.plist`. Building requires
the Swift compiler from Command Line Tools; no package download is needed.

Keep the butterfly key on raw key code **109** (F18) in Chrysalis. Press it
with Chrome in front, then with iTerm in front. Each press should select a
fresh Codex tab in Herdr. Press Fun+3 to open Mission Control. A held key
runs its action only once until released; the two keys track releases
independently.

Press Fun+4 to open Spotlight. If the helper requests permission to send
keyboard events, enable it in Accessibility, restart the loaded helper,
and press Fun+4 again:

```sh
launchctl kickstart -k "gui/$(id -u)/com.mpallone.codex-hotkey"
```

The running helper did not recognize the new grant until restarted. F4
uses macOS's configured Spotlight shortcut (Command+Space by default);
it logs an error if that shortcut is disabled.

## Keep Fun+3 and Control+Up available

The Model 100's Fun key temporarily selects its function layer. In the
stored keyboard map, layer 2 assigns raw key code **60** (F3) to the 3 key.
This matches [Keyboardio's default function layer](https://github.com/keyboardio/Kaleidoscope/blob/master/examples/Devices/Keyboardio/Model100/Model100.ino#L293).

Karabiner previously supplied a default
[F3 → Mission Control translation](https://github.com/pqrs-org/Karabiner-Elements/blob/main/src/share/core_configuration/details/profile.hpp#L105).
This helper restores that translation by opening macOS's built-in
`/System/Applications/Mission Control.app` when F3 is pressed. The existing
Control+Up Mission Control shortcut remains available.

Bare F3 and F4 are reserved systemwide, so these keys on other keyboards
also open Mission Control and Spotlight. Verify Fun+3 with
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

The log should contain registrations for F18 (Codex), F3 (Mission Control),
and F4 (Spotlight). Registration failures and
launcher errors are logged. A conflicting global key binding must be
removed from the other app before this helper can register it. If F3 or F4
registration fails, the helper keeps the Codex binding running.

To stop it and prevent startup at login:

```sh
launchctl bootout "gui/$(id -u)/com.mpallone.codex-hotkey"
rm ~/Library/LaunchAgents/com.mpallone.codex-hotkey.plist
```

The app bundle and launcher can remain installed. The Quick Action and
existing Herdr sessions are preserved.
