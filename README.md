To set up unix env on new computer, do:

1. Set up ssh keys:
   http://www.linuxproblem.org/art_9.html

2. Zip the unix-config directory
3. Zip the scripts directory

4. scp unix-config.zip and scripts.zip
   onto the new machine

5. unzip the files:
   `unzip unix-config.zip # ubuntu`
   `unzip scripts.zip #ubuntu`

6. Configure Bash so iTerm and command-line tools load the same environment:

   ```bash
   chsh -s /bin/bash
   ```

   In iTerm, select **Profiles → General → Command → Login shell**. Put shared
   shell setup in `~/.bashrc`, including the personal dotfiles:

   ```bash
   shopt -s expand_aliases

   source "$HOME/src/mpallone/dotfiles/my-env.sh"
   ```

   `expand_aliases` keeps files that define and invoke aliases working when
   Codex starts non-interactive login shells. Guard interactive-only commands;
   for example, use `[[ $- == *i* ]] && clear` instead of unconditional `clear`.

   Make login shells load that shared setup from `~/.bash_profile`:

   ```bash
   [[ -f "$HOME/.bashrc" ]] && source "$HOME/.bashrc"
   ```

   Do not source `~/.bash_profile` from `~/.bashrc`; reversing the relationship
   makes login and non-login shells behave differently and creates a source loop
   once `~/.bash_profile` loads `~/.bashrc`. Keep credentials and machine-only
   settings in the untracked home files, not this repository.

7. Add everything in the dot_gitconfig file
   into the new machine's .gitconfig file.
   If one doesn't exist, just type
   `cp dot_gitconfig ~/.gitconfig`

8. Sanity check that the .gitconfig
   settings are appropriate for the new
   machine. 

9. Edit one-time-config.sh as appropriate
   for the new machine, and then run it

10. Add everything in the dot_emacs file
   into the new machine's .emacs file.
   If one doesn't exist, just type
   `cp dot_emacs ~/.emacs`

11. Symlink `dot_vimrc` to `~/.vimrc`.
    From the dotfiles repo root:
    `ln -s "$(pwd)/dot_vimrc" ~/.vimrc`

12. Set up Sublime Text keybinds.

13. Set up git diff highlighting: https://stackoverflow.com/questions/5326008/highlight-changed-lines-and-changed-bytes-in-each-changed-line/15149253#15149253  / https://stackoverflow.com/a/55891251 

14. Set up the 'subl' command.

15. Follow the instructions in the README of the sublime-text directory

16. Set up intellij idea CLI: https://www.jetbrains.com/help/idea/working-with-the-ide-features-from-command-line.html 

17. Load the iterm profile I have saved in iCloud

18. Since I generally want work `agent.md` files to reference this repo,
    if I'm setting up a new laptop, then ensure that that `agent.md`
    file knows how to find my ai-rules directory. 

19. Set up the Keyboardio Model 100 butterfly key (opens a fresh Codex tab
    inside herdr, reusing one iTerm tab): install herdr and follow the
    [Karabiner setup instructions](karabiner/README.md). This also depends on the keyboard's own
    firmware -- the butterfly key must be set to raw key code 109 and the Any
    key must be set to raw key code 110 in Chrysalis. Shift-Any opens a new
    Google Chrome tab, and Shift-butterfly opens a new Safari tab, without
    separate Chrysalis mappings.

## AI config & skills distribution

The `ai/` tree is the single source of truth for my Claude context and skills, and
it's distributed to every Claude surface from there:

- **Local Claude Code** — `mmm` (marks-markdown-manager) deploys context + skills.
- **claude.ai app + Cloud Claude Code** — the app has no upload API, so a GitHub Action
  auto-builds ready-to-upload skill ZIPs (published to the `skills-latest` release);
  you drop them into Settings → Skills. That one upload also feeds cloud Code.
- **Cloud Claude Code (alternative)** — `ai/cloud-setup.sh`, run from the environment's
  Setup script, pulls skills **and** AGENTS.md straight from this repo. Redundant with the
  zip path above (they can drift) — kept on purpose.

The intent, the "why", and the exact steps live in [`ai/README.md`](ai/README.md).
