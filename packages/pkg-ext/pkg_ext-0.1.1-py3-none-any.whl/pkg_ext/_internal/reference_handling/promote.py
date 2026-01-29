from __future__ import annotations

import fnmatch
import logging
import re
from typing import TYPE_CHECKING

from pkg_ext._internal.changelog import (
    GroupModuleAction,
    KeepPrivateAction,
    MakePublicAction,
    parse_changelog_actions,
)
from pkg_ext._internal.models import RefSymbol
from pkg_ext._internal.reference_handling.added import get_or_prompt_group

if TYPE_CHECKING:
    from pkg_ext._internal.context import pkg_ctx
    from pkg_ext._internal.models import PkgCodeState

logger = logging.getLogger(__name__)

PromotableEntry = tuple[KeepPrivateAction | None, RefSymbol]


def match_symbol_in_code(private: KeepPrivateAction, code_state: PkgCodeState) -> RefSymbol | None:
    for ref in code_state.import_id_refs.values():
        if ref.name == private.name and ref.local_id == private.full_path:
            return ref
    return None


def find_private_symbols(ctx: pkg_ctx) -> list[PromotableEntry]:
    all_actions = parse_changelog_actions(ctx.settings.changelog_dir)

    already_public = {action.name for action in all_actions if isinstance(action, MakePublicAction)}
    private_entries = [action for action in all_actions if isinstance(action, KeepPrivateAction)]

    result: list[PromotableEntry] = []
    for entry in private_entries:
        if entry.name in already_public:
            continue
        if ref := match_symbol_in_code(entry, ctx.code_state):
            result.append((entry, ref))
    return result


def find_undecided_symbols(ctx: pkg_ctx) -> list[PromotableEntry]:
    undecided = ctx.tool_state.added_refs(ctx.code_state.named_refs)
    return [(None, state.symbol) for state in undecided.values()]


def filter_by_module(entries: list[PromotableEntry], module_prefix: str) -> list[PromotableEntry]:
    return [(e, r) for e, r in entries if r.module_path.startswith(module_prefix)]


def filter_by_pattern(entries: list[PromotableEntry], pattern: str) -> list[PromotableEntry]:
    regex = fnmatch.translate(pattern)
    compiled = re.compile(regex)
    return [(e, r) for e, r in entries if compiled.match(r.name)]


def promote_symbols(
    ctx: pkg_ctx,
    selected: list[PromotableEntry],
    group_name: str | None,
) -> list[MakePublicAction]:
    groups = ctx.tool_state.groups
    pkg_path = ctx.tool_state.pkg_path
    actions: list[MakePublicAction] = []
    created_groups: set[str] = set()

    for private, ref in selected:
        if group_name:
            target_group = group_name
            if target_group not in created_groups and target_group not in groups.name_to_group:
                ctx.add_changelog_action(GroupModuleAction(name=target_group, module_path=ref.module_path))
                created_groups.add(target_group)
        else:
            target_group, group_action = get_or_prompt_group(groups, ref, pkg_path)
            if group_action and target_group not in created_groups:
                ctx.add_changelog_action(group_action)
                created_groups.add(target_group)

        details = f"promoted from private ({private.full_path})" if private else f"created in {ref.rel_path}"
        action = MakePublicAction(name=ref.name, group=target_group, full_path=ref.local_id, details=details)
        ctx.add_changelog_action(action)
        actions.append(action)
        logger.info(f"Promoted {ref.name} to group '{target_group}'")

    return actions


def find_promotable(
    ctx: pkg_ctx,
    name: str | None = None,
    module_filter: str | None = None,
    pattern: str | None = None,
    include_undecided: bool = False,
) -> list[PromotableEntry]:
    results: list[PromotableEntry] = []

    results.extend(find_private_symbols(ctx))

    if include_undecided:
        results.extend(find_undecided_symbols(ctx))

    if not results:
        msg = "No promotable symbols found"
        if not include_undecided:
            msg += " (use --undecided to include symbols without changelog entry)"
        logger.info(msg)
        return []

    if name:
        results = [(e, r) for e, r in results if r.name == name]
    if module_filter:
        results = filter_by_module(results, module_filter)
    if pattern:
        results = filter_by_pattern(results, pattern)

    return results


def handle_promote(
    ctx: pkg_ctx,
    name: str | None = None,
    group: str | None = None,
    module_filter: str | None = None,
    pattern: str | None = None,
    include_undecided: bool = False,
) -> list[MakePublicAction]:
    # Local import required: reference_handling/__init__.py -> added.py -> cli creates circular import
    from pkg_ext._internal import interactive

    promotable = find_promotable(ctx, name, module_filter, pattern, include_undecided)
    if not promotable:
        logger.warning("No symbols found matching criteria")
        return []

    if name and len(promotable) == 1:
        selected = promotable
    else:
        selected = interactive.select_private_symbols(promotable)

    if not selected:
        logger.info("No symbols selected for promotion")
        return []

    return promote_symbols(ctx, selected, group)
