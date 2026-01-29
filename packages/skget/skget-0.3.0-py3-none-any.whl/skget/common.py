import os

REPO_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE_BASE: str = os.path.expanduser("~/.claude")
CODEX_BASE: str = os.path.expanduser("~/.codex")
