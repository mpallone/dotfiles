# Sublime Text configuration

Symlink these files into Sublime Text's `Packages/User` directory so the config
stays in this repository:

- `Preferences.sublime-settings` disables NeoVintageous and Vintage to use
  Sublime's default editing keys, and saves display and indexing preferences.
- `Default (OSX).sublime-keymap` adds the custom mark shortcuts.
- `Default.sublime-mousemap` makes Control-click jump to a definition.

## Install with symlinks

On an existing machine, compare local copies with these files and merge any
settings you want to keep into the repository first. The commands below replace
existing copies or links with symlinks.

Run from the dotfiles repository root:

```bash
sublime_user="$HOME/Library/Application Support/Sublime Text 3/Packages/User"
mkdir -p "$sublime_user"

for config in Preferences.sublime-settings 'Default (OSX).sublime-keymap' Default.sublime-mousemap; do
    ln -sfn "$PWD/sublime-text/$config" "$sublime_user/$config"
done
```

This Mac uses `Sublime Text 3`. On another Mac, open **Preferences → Browse
Packages** and set `sublime_user` to the `User` directory inside the folder that
opens; a fresh installation can use `Sublime Text` instead.

For example, changing `font_size` in the repository's preferences file changes
the file Sublime reads through the link. Keep the checkout at a stable path, and
commit and push config edits to preserve them on other machines.
