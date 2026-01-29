import os
import re

from tabulate import tabulate

from .common import (
    CLAUDE_BASE,
    CODEX_BASE,
)
from .settings import get_skills_roots, resolve_skills_root

import click

CLAUDE_SKILLS_ROOT: str = os.path.join(CLAUDE_BASE, "skills")
CODEX_SKILLS_ROOT: str = os.path.join(CODEX_BASE, "skills")


def _available_skills() -> list[tuple[str, str]]:
    skills: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    for skills_root in get_skills_roots():
        if not os.path.isdir(skills_root):
            continue
        for entry in os.listdir(skills_root):
            if entry.startswith("."):
                continue
            entry_path = os.path.join(skills_root, entry)
            if entry_path in seen_paths:
                continue
            if os.path.isdir(entry_path) and os.path.isfile(
                os.path.join(entry_path, "SKILL.md")
            ):
                skills.append((entry, entry_path))
                seen_paths.add(entry_path)
    return sorted(skills, key=lambda item: (item[0], item[1]))


def _installed_destinations(skill_name: str, skill_path: str) -> list[str]:
    destinations: list[str] = []
    for label, root in (
        ("claude", CLAUDE_SKILLS_ROOT),
        ("codex", CODEX_SKILLS_ROOT),
    ):
        target_path = os.path.join(root, skill_name)
        if not os.path.islink(target_path):
            continue
        resolved = os.path.realpath(target_path)
        if os.path.realpath(skill_path) == resolved:
            destinations.append(label)
    return destinations


def _resolve_skill_path(skill_name: str, source_root: str | None = None) -> str:
    if source_root:
        resolved_root = resolve_skills_root(source_root)
        if not os.path.isdir(resolved_root):
            raise RuntimeError(f"invalid source root: {source_root}")
        candidate = os.path.join(resolved_root, skill_name)
        if os.path.isdir(candidate) and os.path.isfile(
            os.path.join(candidate, "SKILL.md")
        ):
            return candidate
        raise RuntimeError(
            f"skill not found in source root: {skill_name} ({resolved_root})"
        )

    for skills_root in get_skills_roots():
        candidate = os.path.join(skills_root, skill_name)
        if os.path.isdir(candidate) and os.path.isfile(
            os.path.join(candidate, "SKILL.md")
        ):
            return candidate
    raise RuntimeError(f"skill not found: {skill_name}")


def _resolve_targets(destination: str) -> list[str]:
    dest = destination.lower()
    if dest == "auto":
        targets: list[str] = []
        if os.path.isdir(CLAUDE_BASE):
            targets.append(CLAUDE_SKILLS_ROOT)
        if os.path.isdir(CODEX_BASE):
            targets.append(CODEX_SKILLS_ROOT)
        if not targets:
            raise RuntimeError("no ~/.claude or ~/.codex directories found")
        return targets
    elif dest == "claude":
        if not os.path.isdir(CLAUDE_BASE):
            raise RuntimeError("~/.claude directory not found")
        return [CLAUDE_SKILLS_ROOT]
    elif dest == "codex":
        if not os.path.isdir(CODEX_BASE):
            raise RuntimeError("~/.codex directory not found")
        return [CODEX_SKILLS_ROOT]
    else:
        raise ValueError(f"invalid destination: {destination}")


def _install_to_root(source_path: str, skill_name: str, target_root: str) -> str:
    os.makedirs(target_root, exist_ok=True)
    target_path = os.path.join(target_root, skill_name)

    if os.path.lexists(target_path):
        if os.path.islink(target_path):
            os.unlink(target_path)
        else:
            raise RuntimeError(f"cannot overwrite existing non-symlink: {target_path}")

    os.symlink(source_path, target_path)
    return target_path


def _uninstall_from_root(skill_name: str, target_root: str) -> str | None:
    target_path = os.path.join(target_root, skill_name)
    if not os.path.lexists(target_path):
        return None
    if not os.path.islink(target_path):
        raise RuntimeError(f"cannot uninstall non-symlink: {target_path}")
    os.unlink(target_path)
    return target_path


def skills_install(
    skill_name: str, destination: str, source_root: str | None = None
) -> list[str]:
    source_path = _resolve_skill_path(skill_name, source_root=source_root)

    target_paths: list[str] = []
    for target_root in _resolve_targets(destination):
        target_paths.append(_install_to_root(source_path, skill_name, target_root))
    return target_paths


def skills_uninstall(
    skill_name: str, destination: str, source_root: str | None = None
) -> list[str]:
    if source_root:
        _resolve_skill_path(skill_name, source_root=source_root)
    target_paths: list[str] = []
    for target_root in _resolve_targets(destination):
        removed = _uninstall_from_root(skill_name, target_root)
        if removed is not None:
            target_paths.append(removed)
    if not target_paths:
        raise RuntimeError(f"skill not installed: {skill_name}")
    return target_paths


def skills_list(
    pattern: str | None = None, installed_only: bool = False
) -> list[tuple[str, str, list[str]]]:
    skills = _available_skills()
    if pattern:
        try:
            matcher = re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"invalid regex: {pattern}") from exc
        skills = [
            (skill_name, skill_path)
            for skill_name, skill_path in skills
            if matcher.search(skill_name)
        ]

    results: list[tuple[str, str, list[str]]] = []
    for skill_name, skill_path in skills:
        destinations = _installed_destinations(skill_name, skill_path)
        if installed_only and not destinations:
            continue
        results.append((skill_name, skill_path, destinations))
    return results


@click.group()
def skills() -> None:
    pass


@skills.command("install")
@click.argument("skill_name")
@click.option(
    "--source-root",
    "source_root",
    default=None,
    help="Override the skills root to install from (path or URL).",
)
@click.option(
    "--dest",
    "-d",
    "destination",
    type=click.Choice(["auto", "claude", "codex"], case_sensitive=False),
    default="auto",
    show_default=True,
)
def skills_install_cmd(skill_name: str, destination: str, source_root: str | None) -> None:
    try:
        for target_path in skills_install(
            skill_name, destination, source_root=source_root
        ):
            click.echo(f"installed {skill_name} -> {target_path}")
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc


@skills.command("uninstall")
@click.argument("skill_name")
@click.option(
    "--source-root",
    "source_root",
    default=None,
    help="Override the skills root to uninstall from (path or URL).",
)
@click.option(
    "--dest",
    "-d",
    "destination",
    type=click.Choice(["auto", "claude", "codex"], case_sensitive=False),
    default="auto",
    show_default=True,
)
def skills_uninstall_cmd(
    skill_name: str, destination: str, source_root: str | None
) -> None:
    try:
        for target_path in skills_uninstall(
            skill_name, destination, source_root=source_root
        ):
            click.echo(f"uninstalled {skill_name} -> {target_path}")
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc


@skills.command("list")
@click.argument("pattern", required=False)
@click.option(
    "--installed",
    is_flag=True,
    default=False,
    help="Only list skills installed in any destination.",
)
def skills_list_cmd(pattern: str | None, installed: bool) -> None:
    try:
        # TODO: show skill description
        rows = []
        for skill_name, skill_path, destinations in skills_list(
            pattern=pattern, installed_only=installed
        ):
            dest_label = ",".join(destinations) if destinations else "-"
            rows.append((skill_name, dest_label, skill_path))

        table = tabulate(
            rows,
            headers=["[skill name]", "[installed]", "[source path]"],
            tablefmt="plain",
        )
        if table:
            click.echo(table)
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
