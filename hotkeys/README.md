# Butterfly launches Codex from any app

Codex Hotkey registers F18 with macOS's systemwide hotkey API and runs the
shared Codex launcher. It starts at login and has no Dock icon. The native
Quick Action remains available as a manual fallback.

```text
butterfly → F18 → Codex Hotkey → new Herdr tab running codex
```

The helper uses Carbon's `RegisterEventHotKey` API, which reserves this one
key instead of monitoring keyboard input. It does not require a Karabiner
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
fresh Codex tab in Herdr. Holding the key creates only one session until
it is released.

The [Services Quick Action](../quick-actions/README.md) depends on the
front app handling its menu shortcut. Chrome and iTerm did not invoke F18
through that route on this Mac. This helper registers the key independently
of those menus, so those apps do not need to forward it.

## Check startup errors or uninstall

```sh
launchctl print "gui/$(id -u)/com.mpallone.codex-hotkey"
tail -n 30 ~/Library/Logs/CodexHotkey.log
```

The log should contain `registered systemwide F18`. Registration failures
and launcher errors are logged. A conflicting global F18 binding must be
removed from the other app before this helper can register it.

To stop it and prevent startup at login:

```sh
launchctl bootout "gui/$(id -u)/com.mpallone.codex-hotkey"
rm ~/Library/LaunchAgents/com.mpallone.codex-hotkey.plist
```

The app bundle and launcher can remain installed. The Quick Action and
existing Herdr sessions are preserved.
