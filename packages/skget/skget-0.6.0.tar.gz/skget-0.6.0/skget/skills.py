import os
import re

from tabulate import tabulate

from .settings import AgentConfig, get_agents, get_skills_roots, resolve_skills_root

import click

LOCAL_LABEL_SUFFIX = "(local)"


SkillEntry = tuple[str, str]
"""(skill_name, skill_path)."""

SkillInstallStatus = tuple[str, str, list[str]]
"""(skill_name, skill_path, destinations)."""


def _label_for(agent: str, scope: str) -> str:
    """Return the destination label for a given agent and scope."""
    if scope == "local":
        return f"{agent}{LOCAL_LABEL_SUFFIX}"
    return agent


def _resolve_agent_name(agents: dict[str, AgentConfig], dest: str) -> str:
    for name in agents:
        if name.lower() == dest.lower():
            return name
    raise ValueError(f"invalid destination: {dest}")


def _available_skills() -> list[SkillEntry]:
    """Return available skills as (skill_name, skill_path)."""
    skills: list[SkillEntry] = []
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
    """Return destination labels where the skill is installed."""
    destinations: list[str] = []
    for agent, config in get_agents().items():
        base_path = config.base_path
        local_base_path = config.local_base_path
        roots = [
            ("global", os.path.join(base_path, "skills")),
            ("local", os.path.join(local_base_path, "skills")),
        ]
        for scope, root in roots:
            target_path = os.path.join(root, skill_name)
            if not os.path.islink(target_path):
                continue
            resolved = os.path.realpath(target_path)
            if os.path.realpath(skill_path) == resolved:
                destinations.append(_label_for(agent, scope))
    return destinations


def _resolve_skill_path(skill_name: str, source_root: str | None = None) -> str:
    """Return the source path for a skill, searching the configured roots."""
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


def _resolve_targets(destination: str, scope: str) -> list[str]:
    """Return target skill roots for a given destination and scope."""
    agents = get_agents()
    dest = destination.lower()
    scope_value = scope.lower()
    if scope_value not in {"global", "local"}:
        raise ValueError(f"invalid scope: {scope}")

    allow_missing = scope_value == "local"

    if dest == "auto":
        targets: list[str] = []
        for agent, config in agents.items():
            base_path = config.local_base_path if scope_value == "local" else config.base_path
            if allow_missing or os.path.isdir(base_path):
                targets.append(os.path.join(base_path, "skills"))
        if not targets:
            label = "local" if scope_value == "local" else "global"
            raise RuntimeError(f"no {label} agent directories found")
        return targets

    agent_name = _resolve_agent_name(agents, destination)
    base_path = (
        agents[agent_name].local_base_path
        if scope_value == "local"
        else agents[agent_name].base_path
    )
    if not allow_missing and not os.path.isdir(base_path):
        raise RuntimeError(f"{base_path} directory not found")
    return [os.path.join(base_path, "skills")]


def _normalize_destination(destination: str) -> str:
    if destination.lower() == "auto":
        return "auto"
    agents = get_agents()
    return _resolve_agent_name(agents, destination)


def _install_to_root(source_path: str, skill_name: str, target_root: str) -> str:
    """Install a skill by creating a symlink in the target root."""
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
    """Uninstall a skill symlink from the target root."""
    target_path = os.path.join(target_root, skill_name)
    if not os.path.lexists(target_path):
        return None
    if not os.path.islink(target_path):
        raise RuntimeError(f"cannot uninstall non-symlink: {target_path}")
    os.unlink(target_path)
    return target_path


def skills_install(
    skill_name: str,
    destination: str,
    source_root: str | None = None,
    scope: str = "global",
) -> list[str]:
    """Install a skill into the selected agent destination and scope."""
    source_path = _resolve_skill_path(skill_name, source_root=source_root)

    target_paths: list[str] = []
    for target_root in _resolve_targets(destination, scope):
        target_paths.append(_install_to_root(source_path, skill_name, target_root))
    return target_paths


def skills_uninstall(
    skill_name: str,
    destination: str,
    source_root: str | None = None,
    scope: str = "global",
) -> list[str]:
    """Uninstall a skill from the selected agent destination and scope."""
    if source_root:
        _resolve_skill_path(skill_name, source_root=source_root)
    target_paths: list[str] = []
    for target_root in _resolve_targets(destination, scope):
        removed = _uninstall_from_root(skill_name, target_root)
        if removed is not None:
            target_paths.append(removed)
    if not target_paths:
        raise RuntimeError(f"skill not installed: {skill_name}")
    return target_paths


def skills_list(
    pattern: str | None = None, installed_only: bool = False
) -> list[SkillInstallStatus]:
    """Return (skill_name, skill_path, destinations) for matching skills."""
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

    results: list[SkillInstallStatus] = []
    for skill_name, skill_path in skills:
        destinations = _installed_destinations(skill_name, skill_path)
        if installed_only and not destinations:
            continue
        results.append((skill_name, skill_path, destinations))
    return results


@click.group()
def skills() -> None:
    """Manage skills for supported agents."""
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
    type=str,
    default="auto",
    show_default=True,
)
@click.option(
    "--scope",
    "scope",
    type=click.Choice(["global", "local"], case_sensitive=False),
    default="global",
    show_default=True,
    prompt="Install scope",
)
def skills_install_cmd(
    skill_name: str, destination: str, source_root: str | None, scope: str
) -> None:
    """Install a skill via the CLI."""
    try:
        destination = _normalize_destination(destination)
        for target_path in skills_install(
            skill_name, destination, source_root=source_root, scope=scope
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
    type=str,
    default="auto",
    show_default=True,
)
@click.option(
    "--scope",
    "scope",
    type=click.Choice(["global", "local"], case_sensitive=False),
    default="global",
    show_default=True,
)
def skills_uninstall_cmd(
    skill_name: str, destination: str, source_root: str | None, scope: str
) -> None:
    """Uninstall a skill via the CLI."""
    try:
        destination = _normalize_destination(destination)
        for target_path in skills_uninstall(
            skill_name, destination, source_root=source_root, scope=scope
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
    """List available skills via the CLI."""
    try:
        # TODO: show skill description
        rows = []
        for skill_name, skill_path, destinations in skills_list(
            pattern=pattern, installed_only=installed
        ):
            dest_label = ", ".join(destinations) if destinations else "-"
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
