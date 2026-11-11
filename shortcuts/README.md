# Butterfly opens a new Codex session

The Keyboardio Model 100 butterfly key runs a native macOS Shortcut that
creates a fresh Codex tab in Herdr and brings its iTerm tab forward. Each
press creates a new Codex session. Karabiner and its driver are not required.

## Install the launcher and Shortcut

Install iTerm, Herdr, and Codex first. `herdr` must be on `PATH` or in
`~/.local/bin`; `codex` must work in a fresh interactive iTerm shell.

From this repository's root:

```sh
bash shortcuts/install.sh
```

The installer links `~/.local/bin/new-codex-session` to the launcher in this
checkout, signs the tracked Shortcut template, and opens its import screen.
Click **Add Shortcut**. If a shortcut with this name already exists, replace
it rather than keeping a second copy.

In **Shortcuts → Settings → Advanced**, enable **Allow Running Scripts** if
it is off. Open **New Codex Session**, then click its Run button. Allow
Shortcuts to control iTerm when macOS asks. A new Codex tab should appear in
Herdr. With Finder in front, choose **Finder → Services → New Codex Session**.
Check that this creates another Codex tab while reusing Herdr's existing
iTerm tab. Verify this menu route before testing the butterfly key;
`shortcuts run` alone does not verify execution through Services.

## Assign the butterfly key

Open the Shortcut's Details panel and choose **Add Keyboard Shortcut**.
Press the butterfly key; it should register as **F18**. In Chrysalis, the
keyboard's configuration app, the butterfly key on Layer 0 must send raw key
code **109** (F18).

Test with another app in front. If macOS will not accept F18, change the
butterfly key in Chrysalis to send **Control+Option+Command+C**, then assign
that combination instead. The physical action remains one butterfly press.

The keyboard binding and macOS permissions are configured on each Mac;
they are not installed by the template. Follow Apple's [keyboard shortcut
instructions](https://support.apple.com/guide/shortcuts-mac/run-a-shortcut-from-a-keyboard-shortcut-apd163eb9f95/mac).

### Add the matching App Shortcut

To also bind the menu command through macOS App Shortcuts, open **System
Settings → Keyboard → Keyboard Shortcuts → App Shortcuts**. Add an entry
for **All Applications**, with menu title **New Codex Session** and shortcut
**Control+Option+Command+C**. Keep the menu title identical to the Shortcut's
name. This is separate from recording the binding inside Shortcuts.

To apply that same setting from the command line:

```sh
defaults write -g NSUserKeyEquivalents -dict-add '"New Codex Session"' '"@~^c"'
```

This changes only the entry for New Codex Session and preserves other App
Shortcuts. Verify the combination in Finder before assigning it to the
butterfly key in Chrysalis.

## Launcher behavior and troubleshooting

The Shortcut contains one **Run Shell Script** action:

```sh
"$HOME/.local/bin/new-codex-session"
```

The launcher selects the default Herdr session's existing iTerm tab, or
opens one if needed. It creates a tab in the focused Herdr workspace and
runs `codex` in the pane's interactive shell, preserving shell aliases.
If no workspace exists, it creates one. Overlapping launches are serialized;
startup failures produce stderr and a macOS notification.

If the Shortcut fails, run `~/.local/bin/new-codex-session` from iTerm to
check the launcher separately. Check **System Settings → Privacy & Security
→ Automation** if Shortcuts cannot control iTerm.

If F18 does nothing, try **Finder → Services → New Codex Session**. If the
menu route also fails, run the Shortcut once from its editor and retry the
menu route before changing the keyboard binding. Finish the restart after
uninstalling Karabiner before troubleshooting its replacement.

The legacy [Karabiner configuration](../karabiner/README.md) remains in this
repository for reference. Its browser and Any-key bindings require
Karabiner; this installer does not recreate them. Karabiner's built-in
uninstaller leaves the tracked launcher intact. Restart after uninstalling
to finish removing its background components.
