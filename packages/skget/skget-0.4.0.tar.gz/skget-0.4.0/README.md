# Skget

A CLI to add skills to your coding agents. Supported:

- Claude Code
- OpenAI Codex CLI
- More TBD

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
  }
}
```

NOTE: the git hub repo URL should be the root path containing the skill folders.
