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

6. in the ~/.bashrc (or whatever),
   add `source ~/unix-config/my-env.sh`

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

19. **Claude Code on the web (claude.ai/code):** a web session clones only the
    project repo, so `~/.claude` from my laptop is absent. To sync this repo's
    `ai/` tree into `~/.claude` on every session, paste this bootstrap into the
    environment's "Setup script" field:

    ```bash
    #!/bin/bash
    git clone --depth 1 https://github.com/mpallone/dotfiles.git /tmp/dotfiles || true
    [ -f /tmp/dotfiles/ai/cloud-setup.sh ] && bash /tmp/dotfiles/ai/cloud-setup.sh || true
    ```

    It clones this (public) repo and runs `ai/cloud-setup.sh`, which copies
    `ai/global-context/AGENTS.md` -> `~/.claude/CLAUDE.md` and everything under
    `ai/skills/` -> `~/.claude/skills/`. Keeping the script in the repo means
    future edits are just a `git push`.

    - Prerequisite: the environment's network policy must allow `github.com`
      (the "Trusted" policy). Under the "None" network policy the clone fails.
      `git` is pre-installed.
    - Refresh caveat: setup scripts run on the FIRST session, then the filesystem
      is snapshotted and the script is SKIPPED on later sessions — so `~/.claude`
      is frozen until the cache rebuilds (editing the setup script or allowed
      hosts, or ~7-day expiry). To force a refresh after pushing dotfiles changes,
      re-save the setup script in the environment UI.
    - Known limitation: `ai/skills/daily-ai-tools-digest.md` is copied but is NOT
      an invocable skill — Claude Code only discovers `<name>/SKILL.md`
      directories, so a bare `.md` under `skills/` is ignored. Wrapping it as a
      proper skill directory is a separate follow-up.
