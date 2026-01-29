# Skget

A CLI to add skills to your coding agents.

![skget](skget-screenshot.png)

## Quickstart

```bash
pip install skget
```

Just type `skget` in your terminal.

## Settings

Skget reads settings from `~/.config/skget/settings.json`.
You can add your own sources of skills. e.g. a local directory or a GitHub repo.

Example:

```json
{
  "paths": {
    "skills": [
      "/path/to/local/skills",
      "https://github.com/anthropics/skills/tree/main/skills",
    ]
  },
  "agents": {
    "codex": {"base_path": "~/.codex", "local_base_path": ".codex"},
    "opencode": {"base_path": "~/.config/opencode", "local_base_path": ".opencode"}
  }
}
```

NOTE: the git hub repo URL should be the root path containing the skill folders.
