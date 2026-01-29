import os

REPO_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE_BASE: str = os.path.expanduser("~/.claude")
CODEX_BASE: str = os.path.expanduser("~/.codex")
PROJECT_ROOT: str = os.path.abspath(os.getcwd())
LOCAL_CLAUDE_BASE: str = os.path.join(PROJECT_ROOT, ".claude")
LOCAL_CODEX_BASE: str = os.path.join(PROJECT_ROOT, ".codex")


def get_local_agent_bases() -> tuple[str, str]:
    """Return local Claude and Codex base paths as (claude_base, codex_base)."""
    return LOCAL_CLAUDE_BASE, LOCAL_CODEX_BASE
