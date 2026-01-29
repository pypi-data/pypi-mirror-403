import logging
from collections import defaultdict
from pathlib import Path
from typing import get_type_hints

from ask_shell._internal._run import run_and_wait
from ask_shell._internal.rich_progress import new_task
from zero_3rdparty.iter_utils import group_by_once

from pkg_ext._internal.changelog import GroupModuleAction, KeepPrivateAction, MakePublicAction
from pkg_ext._internal.cli.options import get_default_editor
from pkg_ext._internal.context import pkg_ctx
from pkg_ext._internal.errors import NoPublicGroupMatch
from pkg_ext._internal.interactive import select_group, select_multiple_refs
from pkg_ext._internal.models import (
    PkgCodeState,
    PublicGroups,
    RefStateWithSymbol,
    RefSymbol,
    SymbolType,
)
from pkg_ext._internal.pkg_state import PkgExtState
from pkg_ext._internal.settings import PkgSettings
from pkg_ext._internal.signature_parser import is_cli_command

logger = logging.getLogger(__name__)


def get_or_prompt_group(groups: PublicGroups, ref: RefSymbol, pkg_path: Path) -> tuple[str, GroupModuleAction | None]:
    """Get group name for ref, prompting if not found. Returns (group_name, optional action)."""
    try:
        group = groups.matching_group(ref)
        groups.add_ref(ref, group.name)
        return group.name, None
    except NoPublicGroupMatch:
        new_group = select_group(groups, ref, pkg_path)
        return new_group.name, GroupModuleAction(name=new_group.name, module_path=ref.module_path)


def ensure_function_args_exposed(
    code_state: PkgCodeState, function_refs: list[RefStateWithSymbol]
) -> dict[RefStateWithSymbol, list[RefSymbol]]:
    func_arg_symbols: dict[RefStateWithSymbol, list[RefSymbol]] = defaultdict(list)
    for func_ref in function_refs:
        func = code_state.lookup(func_ref.symbol)
        type_hints = get_type_hints(func)
        for name, type in type_hints.items():
            if local_ref := code_state.as_local_ref(type):
                logger.info(f"auto exposing arg {name} on func {func_ref.name}")
                func_arg_symbols[func_ref].append(local_ref)
    return func_arg_symbols


def _expose_ref(ctx: pkg_ctx, groups: PublicGroups, ref: RefSymbol, details: str, pkg_path: Path) -> None:
    group_name, group_action = get_or_prompt_group(groups, ref, pkg_path)
    if group_action:
        ctx.add_changelog_action(group_action)
    ctx.add_changelog_action(MakePublicAction(name=ref.name, group=group_name, full_path=ref.local_id, details=details))


def _expose_function_args(
    ctx: pkg_ctx,
    tool_state: PkgExtState,
    code_state: PkgCodeState,
    exposed: list[RefStateWithSymbol],
) -> list[RefSymbol]:
    groups = tool_state.groups
    pkg_path = tool_state.pkg_path
    arg_refs_all: list[RefSymbol] = []
    args_exposed = ensure_function_args_exposed(code_state, exposed)
    for func_ref, arg_refs in args_exposed.items():
        arg_refs_all.extend(arg_refs)
        for ref in arg_refs:
            if tool_state.has_decision(ref.name):
                continue
            _expose_ref(
                ctx,
                groups,
                ref,
                f"exposed in the function {func_ref.symbol.local_id}",
                pkg_path,
            )
    return arg_refs_all


def _is_cli_command_ref(code_state: PkgCodeState, ref: RefStateWithSymbol) -> bool:
    func = code_state.lookup(ref.symbol)
    return is_cli_command(func)


def _partition_cli_refs(
    code_state: PkgCodeState,
    file_states: list[RefStateWithSymbol],
) -> tuple[list[RefStateWithSymbol], list[RefStateWithSymbol]]:
    cli_commands = [s for s in file_states if _is_cli_command_ref(code_state, s)]
    non_cli = [s for s in file_states if s not in cli_commands]
    return cli_commands, non_cli


def _auto_expose_cli_commands(
    ctx: pkg_ctx,
    groups: PublicGroups,
    pkg_path: Path,
    rel_path: str,
    cli_commands: list[RefStateWithSymbol],
) -> None:
    for ref in cli_commands:
        logger.info(f"Auto-exposing CLI command: {ref.name}")
        _expose_ref(ctx, groups, ref.symbol, f"CLI command in {rel_path}", pkg_path)


def _prompt_and_expose(
    ctx: pkg_ctx,
    groups: PublicGroups,
    pkg_path: Path,
    rel_path: str,
    non_cli: list[RefStateWithSymbol],
    symbol_type: str,
    settings: PkgSettings,
) -> list[RefStateWithSymbol]:
    if not non_cli:
        return []

    if not settings.skip_open_in_editor:
        run_and_wait(f"{get_default_editor()} {pkg_path / rel_path}")

    exposed = select_multiple_refs(
        f"Select references of type {symbol_type} to expose from {rel_path} (if any):",
        non_cli,
    )
    for ref in exposed:
        _expose_ref(ctx, groups, ref.symbol, f"created in {rel_path}", pkg_path)

    for ref in non_cli:
        if ref not in exposed:
            ctx.add_changelog_action(KeepPrivateAction(name=ref.name, full_path=ref.symbol.local_id))

    return exposed


def make_expose_decisions(
    refs: dict[str, list[RefStateWithSymbol]],
    ctx: pkg_ctx,
    tool_state: PkgExtState,
    code_state: PkgCodeState,
    symbol_type: str,
    settings: PkgSettings,
) -> list[RefStateWithSymbol | RefSymbol]:
    decided_refs: list[RefStateWithSymbol | RefSymbol] = []
    groups = tool_state.groups
    pkg_path = tool_state.pkg_path

    for rel_path, file_states in refs.items():
        if symbol_type == SymbolType.FUNCTION:
            cli_commands, non_cli = _partition_cli_refs(code_state, file_states)
            _auto_expose_cli_commands(ctx, groups, pkg_path, rel_path, cli_commands)
        else:
            cli_commands, non_cli = [], file_states

        exposed = _prompt_and_expose(ctx, groups, pkg_path, rel_path, non_cli, symbol_type, settings)

        all_exposed = cli_commands + exposed
        if all_exposed and symbol_type == SymbolType.FUNCTION:
            decided_refs.extend(_expose_function_args(ctx, tool_state, code_state, all_exposed))

    return decided_refs


def _keep_all_private(ctx: pkg_ctx, added_refs: dict[str, RefStateWithSymbol]) -> None:
    for ref in added_refs.values():
        ctx.add_changelog_action(KeepPrivateAction(name=ref.name, full_path=ref.symbol.local_id))
    logger.info(f"Kept {len(added_refs)} new references private")


def _sort_by_dep_order(
    code_state: PkgCodeState,
    rel_path_refs: dict[str, list[RefStateWithSymbol]],
) -> dict[str, list[RefStateWithSymbol]]:
    sorted_rel_paths = code_state.sort_rel_paths_by_dependecy_order(rel_path_refs.keys(), reverse=True)
    return {rel_path: rel_path_refs[rel_path] for rel_path in sorted_rel_paths}


TRACKED_SYMBOL_TYPES = (SymbolType.FUNCTION, SymbolType.CLASS, SymbolType.EXCEPTION)


def handle_added_refs(ctx: pkg_ctx) -> None:
    tool_state = ctx.tool_state
    code_state = ctx.code_state
    added_refs = tool_state.added_refs(code_state.named_refs)
    if not added_refs:
        logger.info("No new references found in the package")
        return

    if ctx.settings.keep_private:
        _keep_all_private(ctx, added_refs)
        return

    with new_task(
        "New References expose/hide decisions",
        total=len(added_refs),
        log_updates=True,
    ) as task:
        for symbol_type in TRACKED_SYMBOL_TYPES:
            relevant_refs = [ref for ref in added_refs.values() if ref.symbol.type == symbol_type]
            if not relevant_refs:
                continue
            file_added = group_by_once(relevant_refs, key=lambda s: s.symbol.rel_path)
            file_added = _sort_by_dep_order(code_state, file_added)
            extra_refs_decided = make_expose_decisions(
                file_added, ctx, tool_state, code_state, symbol_type, ctx.settings
            )
            all_refs_decided = relevant_refs + extra_refs_decided
            for ref in all_refs_decided:
                added_refs.pop(ref.name, None)
            task.update(advance=len(all_refs_decided))
    if added_refs:
        remaining_str = "\n".join(str(ref) for ref in added_refs.values())
        untracked = [s for s in SymbolType if s not in TRACKED_SYMBOL_TYPES]
        logger.debug(f"still has {len(added_refs)}, untracked symbol types: {untracked} remaining:\n{remaining_str}")
