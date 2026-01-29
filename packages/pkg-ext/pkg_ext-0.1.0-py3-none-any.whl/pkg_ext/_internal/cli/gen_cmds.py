"""Generation commands: gen_examples, gen_tests, gen_docs."""

import logging
from pathlib import Path

import typer

from pkg_ext._internal.cli.options import option_group, option_output_dir
from pkg_ext._internal.cli.workflow_cmds import (
    generate_docs_for_pkg,
    generate_examples_for_groups,
    generate_tests_for_groups,
)
from pkg_ext._internal.cli.workflows import create_api_dump
from pkg_ext._internal.settings import PkgSettings

logger = logging.getLogger(__name__)


def gen_examples(
    ctx: typer.Context,
    group: str | None = option_group,
):
    """Generate example files for public API functions."""
    settings: PkgSettings = ctx.obj
    api_dump = create_api_dump(settings)
    groups = [api_dump.get_group(group)] if group else api_dump.groups
    generate_examples_for_groups(settings, groups)


def gen_tests(
    ctx: typer.Context,
    group: str | None = option_group,
):
    """Generate parameterized test files from examples."""
    settings: PkgSettings = ctx.obj
    api_dump = create_api_dump(settings)
    groups = [api_dump.get_group(group)] if group else api_dump.groups
    generate_tests_for_groups(settings, groups)


def gen_docs(
    ctx: typer.Context,
    output_dir: Path | None = option_output_dir,
    group: str | None = option_group,
):
    """Generate documentation from public API."""
    settings: PkgSettings = ctx.obj
    count = generate_docs_for_pkg(settings, output_dir=output_dir, filter_group=group)
    docs_dir = output_dir or settings.docs_dir
    logger.info(f"Generated {count} doc files in {docs_dir}")
