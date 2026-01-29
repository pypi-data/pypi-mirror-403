"""Changelog commands: chore, promote, release_notes."""

import logging
from pathlib import Path

import typer
from zero_3rdparty.file_utils import ensure_parents_write_text

from pkg_ext._internal.changelog import (
    ChoreAction,
    ReleaseAction,
    changelog_filepath,
    dump_changelog_actions,
    parse_changelog_actions,
    parse_changelog_file_path,
)
from pkg_ext._internal.changelog.write_changelog_md import read_changelog_section
from pkg_ext._internal.cli.workflows import (
    GenerateApiInput,
    create_ctx,
    write_generated_modules,
)
from pkg_ext._internal.git_usage import GitSince, find_pr_info_or_none
from pkg_ext._internal.settings import PkgSettings
from pkg_ext._internal.version_bump import read_current_version

logger = logging.getLogger(__name__)


def _get_current_pr_number(settings: PkgSettings) -> int:
    pr_info = find_pr_info_or_none(settings.repo_root)
    return pr_info.pr_number if pr_info else 0


def _create_chore_action(settings: PkgSettings, pr_number: int, description: str):
    changelog_path = changelog_filepath(settings.changelog_dir, pr_number)
    existing = parse_changelog_file_path(changelog_path) if changelog_path.exists() else []
    action = ChoreAction(description=description)
    dump_changelog_actions(changelog_path, existing + [action])
    logger.info(f"Created chore action in {changelog_path.name}: {description}")


def chore(
    ctx: typer.Context,
    description: str = typer.Option(
        ...,
        "--description",
        "-d",
        help="Description of internal changes (e.g., 'CI improvements', 'Dependency updates')",
    ),
    pr_number: int = typer.Option(
        0,
        "--pr",
        help="PR number (auto-detected from current branch if not provided)",
    ),
):
    """Create a ChoreAction for internal changes that warrant a release."""
    settings: PkgSettings = ctx.obj
    pr = pr_number or _get_current_pr_number(settings)
    if not pr:
        logger.error("Could not detect PR number. Use --pr to specify it.")
        raise typer.Exit(1)
    _create_chore_action(settings, pr, description)


def promote(
    ctx: typer.Context,
    name: str | None = typer.Option(None, "--name", "-n", help="Symbol name to promote"),
    group: str | None = typer.Option(None, "--group", "-g", help="Target group"),
    module_filter: str | None = typer.Option(
        None, "--module", "-m", help="Filter by module path prefix (inside the package, don't include the package name)"
    ),
    pattern: str | None = typer.Option(None, "--pattern", "-p", help="Filter by name pattern (e.g., 'dump_*')"),
    undecided: bool = typer.Option(
        False,
        "--undecided",
        "-u",
        help="Include symbols without changelog entry (not yet decided)",
    ),
    pr_number: int = typer.Option(0, "--pr", help="PR number (auto-detected if not provided)"),
):
    """Promote symbols to public API (private or undecided)."""
    from pkg_ext._internal.reference_handling.promote import handle_promote

    settings: PkgSettings = ctx.obj
    pr = pr_number or _get_current_pr_number(settings)
    if not pr:
        logger.error("Could not detect PR number. Use --pr to specify it.")
        raise typer.Exit(1)

    api_input = GenerateApiInput(
        settings=settings,
        git_changes_since=GitSince.NO_GIT_CHANGES,
        bump_version=False,
        create_tag=False,
        push=False,
        explicit_pr=pr,
    )
    pkg_ctx = create_ctx(api_input)

    with pkg_ctx:
        actions = handle_promote(pkg_ctx, name, group, module_filter, pattern, undecided)

    if actions:
        version = str(read_current_version(pkg_ctx))
        write_generated_modules(pkg_ctx, version)
        logger.info(f"Promoted {len(actions)} symbol(s) to public API")
    else:
        logger.info("No symbols promoted")


def find_release_action(changelog_dir: Path, version: str) -> ReleaseAction:
    for changelog_action in parse_changelog_actions(changelog_dir):
        if isinstance(changelog_action, ReleaseAction) and changelog_action.name == version:
            pr = changelog_action.pr
            assert pr, f"found changelog action: {changelog_action} but pr missing"
            return changelog_action
    raise ValueError(f"couldn't find a release for {version}")


def release_notes(
    ctx: typer.Context,
    tag_name: str = typer.Option(..., "--tag", help="tag to find release notes for"),
):
    settings: PkgSettings = ctx.obj
    version = tag_name.removeprefix(settings.tag_prefix)
    action = find_release_action(settings.changelog_dir, version)
    content = read_changelog_section(
        settings.changelog_md.read_text(),
        old_version=action.old_version,
        new_version=action.name,
    )
    output_file = settings.repo_root / f"dist/{tag_name}.changelog.md"
    ensure_parents_write_text(output_file, content)
