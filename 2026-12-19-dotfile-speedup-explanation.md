# Dotfile Cleanup & Speedup - 2026-01-19

This file documents changes made to the shell environment configuration to resolve startup errors and improve terminal responsiveness.

## 1. Resolved `fatal: not a git repository` Errors

### Problem
Opening a new terminal resulted in multiple `fatal: not a git repository` errors.
This was caused by two issues:
1.  **Broken `cicd` tool:** The `.bash_profile` was trying to source a `cicd` tool that depended on a missing Python `git` module.
2.  **Bad Git Aliases:** In `my-env.sh`, aliases like `alias pullcb="git pull origin 
currgb
"` were executing `currgb` (which runs `git rev-parse`) **immediately** at shell startup. If the home directory wasn't a git repo, this failed.

### Fix
*   **`cicd`:** Removed the `eval "$(_CICD_COMPLETE=source cicd))"` line and related exports from `.bash_profile` and `riot-env.sh`.
*   **Git Aliases:** Refactored aliases in `my-env.sh` to use single quotes (deferring execution) and converted the `currgitbranch` alias into a shell function.
    *   *Old:* `alias pullcb="git pull origin 
currgb
"` (Runs immediately)
    *   *New:* `alias pullcb='git pull origin $(currgitbranch)'` (Runs only when typed)

## 2. Improved Terminal Startup Speed (NVM Lazy Load)

### Problem
The terminal took 1-2 seconds to become ready.
The culprit was `nvm` (Node Version Manager) initialization in `.bashrc`. The standard `nvm.sh` script is slow because it scans directories and modifies the `$PATH` every time a shell opens.

### Fix
Implemented "Lazy Loading" for `nvm` in `.bashrc`.
*   Removed the standard initialization lines.
*   Added wrapper functions for `node`, `npm`, and `nvm`.
*   **How it works:** When you open a terminal, `nvm` is **not** loaded. The terminal opens instantly. The first time you run `node`, `npm`, or `nvm`, the wrapper function detects this, loads the full `nvm` environment, and then runs your command.

## 3. General Cleanup

### Gandalf
*   Removed duplicate `Gandalf` auto-completion entries in `.bash_profile`.
*   Removed the `GANDALF_ENABLE_AUTOUPGRADE` export to prevent potential network calls/delays during startup.

### Files Modified
*   `~/.bash_profile`
*   `~/.bashrc`
*   `~/src/mpallone/dotfiles/my-env.sh`
*   `~/src/riot/mpallone/dotfiles/riot-env.sh`

*(Original commands have been preserved in these files as comments for reference.)*
