# Butterfly opens a new Codex session

For a key that works with Chrome, iTerm, or another app in front, use the
[systemwide hotkey helper](../hotkeys/README.md). This Quick Action remains
the Services-menu fallback; its keyboard route depends on the front app.

The Keyboardio Model 100 butterfly key runs **Launch Codex Session**, a
native macOS Quick Action: an Automator workflow available in the Services
menu. It brings Herdr's iTerm tab forward and creates a fresh Codex tab.
Karabiner and its driver are not required.

```text
butterfly → F18 → Launch Codex Session → new Herdr tab running codex
```

## Install the Quick Action and F18 binding

Install iTerm, Herdr, and Codex first. `herdr` must be on `PATH` or in
`~/.local/bin`, and `codex` must work in an interactive iTerm shell.
From this repository's root:

```sh
bash quick-actions/install.sh
```

The installer links the workflow into `~/Library/Services` and the shared
launcher into `~/.local/bin/new-codex-session`. It assigns bare F18 to this
one service and refreshes macOS's Services registry. Other service bindings
are preserved. It does not import a Shortcut or install a background app.

In Chrysalis, the keyboard's configuration app, the butterfly key on Layer
0 must send raw key code **109** (F18). No modifier chord is required.

With Finder in front, choose **Finder → Services → Launch Codex Session**.
Allow macOS to control iTerm if prompted. Then press butterfly and confirm
that another Codex tab opens in Herdr while the same iTerm tab is reused.
Also test with the apps where you expect to use the key; Services availability
depends on the front application.

## Keep the launch routes distinct

The older **New Codex Session** item belongs to the optional
[Shortcuts-app setup](../shortcuts/README.md). Its menu route worked, but
its recorded keyboard bindings did not reliably launch on this Mac.
**Launch Codex Session** is the Quick Action installed here.

The Quick Action calls the same
[`new-codex-session.sh`](../shortcuts/new-codex-session.sh) launcher as the
Shortcuts-app setup. The legacy
[`karabiner/scripts/codex-tab.sh`](../karabiner/scripts/codex-tab.sh) path
also links to that launcher. Fixes to launch behavior belong in that one
shared script.

If launching fails, run `~/.local/bin/new-codex-session` in iTerm to check
the launcher separately. If the menu works but F18 does not, rerun the
installer and inspect **System Settings → Keyboard → Keyboard Shortcuts →
Services** for **Launch Codex Session**. Its binding should be F18 alone.
