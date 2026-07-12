## 📦 What this is

Auto-built, upload-ready skill ZIPs for the **claude.ai app**. Rebuilt on every
push to `main`. Currently includes: `teach-me`, `jira-sprint-cleanup`.

---

## ✅ Install / update (covers the app **and** Cloud Claude Code)

1. **Download** the `.zip`(s) below.
2. claude.ai → **Settings → Capabilities** → turn on **"Code execution and file creation."**
3. **Settings → Skills** → **Upload** each zip → **toggle it ON.**
4. Done. Enabling a skill in the app also auto-loads it into **Cloud Claude Code**
   sessions (claude.ai/code) — no separate step.

- 🔁 **When a skill changes:** a fresh zip lands here automatically — just re-upload it.
- 🔌 `jira-sprint-cleanup` needs your **Atlassian connector** enabled in the chat.

---

## 💻 Local Claude Code

Nothing to do here. Local is handled by **`mmm`** (marks-markdown-manager) straight
from the repo — run your usual `mmm deploy`.

---

## ⚠️ AGENTS.md is NOT in these zips — update it BY HAND

Global context (`ai/global-context/AGENTS.md`) does **not** ride along with skills.
Whenever you change it, update it manually in **both** places:

- **Claude app:** paste it into **Settings → Profile → your personal preferences /
  custom instructions.**
- **Cloud Claude Code:** if you've wired up the `ai/cloud-setup.sh` bootstrap in the
  environment's Setup script, AGENTS.md is pulled in automatically (re-save the setup
  script to refresh). Otherwise, paste the guidance into the work repo's `CLAUDE.md`.

_(Local Claude Code gets AGENTS.md via `mmm`, so that one's already covered.)_

---

_The intent and full architecture live in [`ai/README.md`](https://github.com/mpallone/dotfiles/blob/main/ai/README.md)._
