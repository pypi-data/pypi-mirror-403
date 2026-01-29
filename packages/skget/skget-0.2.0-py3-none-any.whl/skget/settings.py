import json
import os
import shutil
import subprocess
from urllib.parse import urlparse

from .common import REPO_ROOT

CONFIG_DIR: str = os.path.expanduser("~/.config/skget")
SETTINGS_PATH: str = os.path.join(CONFIG_DIR, "settings.json")
DEFAULT_SETTINGS_PATH: str = os.path.join(REPO_ROOT, "default.settings.json")


def _run_git(args: list[str], cwd: str | None = None) -> None:
    try:
        subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git is required to clone skills from URL") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        msg = "git command failed"
        if detail:
            msg = f"{msg}: {detail}"
        raise RuntimeError(msg) from exc


def _parse_github_tree_url(url: str) -> tuple[str, str, str, str, str | None, str]:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise RuntimeError(f"invalid github skills url: {url}")
    owner = parts[0]
    repo = parts[1]
    repo_name = repo[:-4] if repo.endswith(".git") else repo
    repo_url = f"{parsed.scheme}://{parsed.netloc}/{owner}/{repo_name}"
    branch = None
    subpath = ""
    if len(parts) >= 4 and parts[2] == "tree":
        branch = parts[3]
        if len(parts) > 4:
            subpath = "/".join(parts[4:])
    return repo_url, parsed.netloc, owner, repo_name, branch, subpath


def _ensure_repo(
    repo_url: str,
    clone_root: str,
    branch: str | None,
    subpath: str,
) -> None:
    if not os.path.isdir(clone_root):
        os.makedirs(os.path.dirname(clone_root), exist_ok=True)
        _run_git(["clone", "--filter=blob:none", "--no-checkout", repo_url, clone_root])
    elif not os.path.isdir(os.path.join(clone_root, ".git")):
        raise RuntimeError(f"existing path is not a git repo: {clone_root}")

    if subpath:
        _run_git(["-C", clone_root, "sparse-checkout", "init", "--cone"])
        _run_git(["-C", clone_root, "sparse-checkout", "set", subpath])

    if branch:
        try:
            _run_git(["-C", clone_root, "checkout", branch])
        except RuntimeError:
            _run_git(["-C", clone_root, "fetch", "origin", branch])
            _run_git(["-C", clone_root, "checkout", branch])
    elif not os.path.isdir(os.path.join(clone_root, ".git", "refs")):
        _run_git(["-C", clone_root, "checkout"])


def resolve_skills_root(entry: str) -> str:
    parsed = urlparse(entry)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        if parsed.netloc.lower() == "github.com":
            repo_url, host, owner, repo, branch, subpath = _parse_github_tree_url(entry)
            clone_root = (
                os.path.join(CONFIG_DIR, host, owner, repo, "tree", branch)
                if branch
                else os.path.join(CONFIG_DIR, host, owner, repo)
            )
            _ensure_repo(repo_url, clone_root, branch, subpath)
            return os.path.join(clone_root, subpath) if subpath else clone_root

        parts = [part for part in parsed.path.split("/") if part]
        if not parts:
            raise RuntimeError(f"invalid skills url: {entry}")
        repo = parts[-1]
        repo_name = repo[:-4] if repo.endswith(".git") else repo
        clone_root = os.path.join(CONFIG_DIR, parsed.netloc, *parts[:-1], repo_name)
        repo_url = (
            f"{parsed.scheme}://{parsed.netloc}/{'/'.join(parts[:-1] + [repo_name])}"
        )
        _ensure_repo(repo_url, clone_root, None, "")
        return clone_root

    expanded = os.path.expanduser(entry)
    return os.path.abspath(expanded)


def _load_settings() -> dict:
    if not os.path.isfile(SETTINGS_PATH):
        if not os.path.isfile(DEFAULT_SETTINGS_PATH):
            return {}
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            shutil.copyfile(DEFAULT_SETTINGS_PATH, SETTINGS_PATH)
        except OSError as exc:
            raise RuntimeError(
                f"unable to write settings file: {SETTINGS_PATH}"
            ) from exc
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid settings file: {SETTINGS_PATH}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"invalid settings file: {SETTINGS_PATH}")
    return data


def get_skills_roots() -> list[str]:
    settings = _load_settings()
    paths = settings.get("paths")
    if isinstance(paths, dict) and "skills" in paths:
        skills_value = paths.get("skills")
        if not isinstance(skills_value, list):
            raise RuntimeError("invalid settings: paths.skills must be a list")
        roots: list[str] = []
        for entry in skills_value:
            if not isinstance(entry, str):
                continue
            roots.append(resolve_skills_root(entry))
        return roots

    fallback = os.path.join(REPO_ROOT, "skills")
    if os.path.isdir(fallback):
        return [fallback]
    return []
