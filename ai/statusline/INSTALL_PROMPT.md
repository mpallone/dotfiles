# Install this Claude Code status line on macOS

Copy and paste the prompt below into Claude Code or another coding assistant while `statusline.py` is available in the same folder.

```text
Install the attached `statusline.py` as my Claude Code status line on macOS.

Requirements:
1. Confirm this is macOS and that `python3` is available. Stop with a clear explanation if either check fails.
2. Copy `statusline.py` to `~/.claude/statusline.py` and make it executable.
3. Keep the cost field labeled in uppercase as `SESSION $1.23` so recipients know it is cumulative for the current Claude Code session, not the last message or Git commit.
4. Preserve every existing field in `~/.claude/settings.json`. Create the file as an empty JSON object only if it does not exist.
5. Add or replace only this setting, using the recipient's resolved absolute home-directory path in the command:

   "statusLine": {
     "type": "command",
     "command": "/usr/bin/python3 /ABSOLUTE/HOME/.claude/statusline.py"
   }

   If `/usr/bin/python3` does not exist, use the absolute path returned by `command -v python3`.
6. Update the JSON atomically and keep it valid. Do not overwrite, reformat manually, or remove unrelated settings.
7. Verify:
   - the script passes Python syntax compilation with its bytecode cache redirected to `/tmp`;
   - the installed script is executable;
   - `settings.json` parses as JSON and contains the exact `statusLine` command;
   - piping representative Claude status JSON into the script prints cost, a 14-character context bar, percent free, Git branch when available, and added/removed line counts.
8. Report the installed paths and verification results. Do not commit or modify any project repository.

Restart Claude Code after installation so it reloads the setting.
```
