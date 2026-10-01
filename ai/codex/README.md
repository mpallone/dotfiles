# Codex CLI configuration

`config.toml` holds the non-sensitive Codex Terminal User Interface (TUI)
defaults that should persist across machines. Merge it into
`~/.codex/config.toml`; the user configuration also contains machine-local
provider, project-trust, and Model Context Protocol (MCP) settings that must
not be committed.

## Allow Sublime Text launches

On macOS, the Codex sandbox blocks Sublime Text's application-launch services.
Install the narrow launcher exception alongside the other user rules:

```bash
mkdir -p ~/.codex/rules
ln -s ~/src/mpallone/dotfiles/ai/codex/rules/sublime.rules ~/.codex/rules/sublime.rules
```

Restart Codex after installing the rule. Editor launches must request
`sandbox_permissions="require_escalated"` and use the full binary path;
the rule allows that command outside the sandbox without a prompt.
The rest of Codex's sandbox remains active. `mmm deploy` deploys the launch
instructions in global context; this rule is installed separately.
