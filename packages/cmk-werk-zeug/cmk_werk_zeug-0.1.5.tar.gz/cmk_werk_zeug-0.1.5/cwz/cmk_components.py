#!/usr/bin/env python3

"""Checkmk-code-owners CLI
* [Brainstorming document](https://docs.google.com/document/d/1Yul9GjAIkJBowWhvIzwRFFtK-GIZfdTKMSllEzF4Juw)
* [Component Matrix Owners File Implementation](https://jira.lan.tribe29.com/browse/CMK-24954)
* [Component Ownership at Checkmk](https://docs.google.com/document/d/11pbv5J6VjdbuwDTUqBLTP2SqWsd5C1AXjgdpfjZupCM)
* [code-owners / REST API](https://android-review.googlesource.com/plugins/code-owners/Documentation/rest-api.html)
"""

# Insights we want to get:
# - what components do exist?
# - who's in charge of a component
# - what files/directories belong to a component
# - how do the provided ownership infos reflect the 'reality' reported by 'git blame'?
# - what components am I owner for?
# - what files am I responsible for?
# - check OWNERS files with per-file only for `set noparent`
# - check for redundant (nested) information

import asyncio
import logging
from argparse import ArgumentParser
from argparse import Namespace as Args
from contextlib import suppress
from typing import ClassVar, ParamSpec

import yaml
from rich import print as rich_print
from rich import traceback
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.suggester import SuggestFromList
from textual.widgets import Header, Input, Tree
from trickkiste.base_tui_app import TuiBaseApp
from trickkiste.logging_helper import apply_common_logging_cli_args, setup_logging
from trickkiste.misc import process_output

from .gerrit_utils.client import (
    CodeOwnersClient,
    GerritClient,
    apply_code_owner_cli_args,
    with_gerrit_client,
)

ArgumentsP = ParamSpec("ArgumentsP")

__version__ = "0.1.0"


def parse_arguments() -> Args:
    """parse command line arguments and return argument object"""

    parser = ArgumentParser(
        "cmk-components",
        description="Provides information about components and code owners",
    )

    apply_common_logging_cli_args(parser)
    # apply_common_gerrit_cli_args(parser)
    apply_code_owner_cli_args(parser)

    parser.set_defaults(func=_fn_tui)

    subparsers = parser.add_subparsers(help="available commands", metavar="CMD")

    parser_tui = subparsers.add_parser("tui", help="Start a TUI (default)")
    parser_tui.set_defaults(func=_fn_tui)

    parser_list = subparsers.add_parser("list", aliases=["ls"], help="List components")
    parser_list.set_defaults(func=_fn_list)
    parser_list.add_argument("-v", "--verbose", action="store_true")

    parser_component_owners_and_members = subparsers.add_parser(
        "members",
        help="[COMPONENT ..] Show owners and members for COMPONENT*",
    )
    parser_component_owners_and_members.set_defaults(func=_fn_component_owners_and_members)
    parser_component_owners_and_members.add_argument(
        "entities", type=str, nargs="*", metavar="COMPONENT"
    )

    parser_component_paths = subparsers.add_parser(
        "component-paths", help="[COMPONENT ..] Show paths for COMPONENT*"
    )
    parser_component_paths.set_defaults(func=_fn_component_paths)
    parser_component_paths.add_argument("entities", type=str, nargs="+", metavar="COMPONENT")

    parser_owners_for = subparsers.add_parser(
        "owners-for", aliases=[], help="[PATH ..] Show component for PATH*"
    )
    parser_owners_for.set_defaults(func=_fn_owners_for)
    parser_owners_for.add_argument("entities", type=str, nargs="+", metavar="PATH")

    parser_component_for_path = subparsers.add_parser(
        "component-for", aliases=[], help="[PATH ..] Show component for PATH*"
    )
    parser_component_for_path.set_defaults(func=_fn_component_for_path)
    parser_component_for_path.add_argument("entities", type=str, nargs="+", metavar="PATH")

    parser_all_code_owners_config_files = subparsers.add_parser(
        "config-files", aliases=[], help="List all owners config files"
    )
    parser_all_code_owners_config_files.set_defaults(func=_fn_all_code_owners_config_files)

    # These have no help text -> don't show up (intentionally)

    parser_project_config = subparsers.add_parser("project-config")
    parser_project_config.set_defaults(func=_fn_project_config)

    # restricted access
    parser_check_config = subparsers.add_parser("check-config")
    parser_check_config.set_defaults(func=_fn_check_config)

    # reference and debug only (will vanish)
    parser_stuff = subparsers.add_parser("stuff")
    parser_stuff.set_defaults(func=_fn_stuff)

    return parser.parse_args()


@with_gerrit_client
async def _fn_list(
    cli_args: Args,
    gerrit_client: GerritClient,  # noqa: ARG001 Unused function argument
    owners_client: CodeOwnersClient,
) -> None:
    for name, details in (await owners_client.all_components_info()).items():
        rich_print(  # fixme(frans): cleanup
            f"[default][bold cyan]{(details.description or '').split('\n')[0]}[/] / ({name})[/]"
            if cli_args.verbose
            else name
        )
        if cli_args.verbose:
            for member in (details.component_owner_email, *(details.code_owners_email or [])):
                rich_print(f" - {member}")


@with_gerrit_client
async def _fn_all_components_info(
    cli_args: Args,  # noqa: ARG001 Unused function argument
    gerrit_client: GerritClient,  # noqa: ARG001 Unused function argument
    owners_client: CodeOwnersClient,
) -> None:
    rich_print(yaml.dump(await owners_client.all_components_info()))


@with_gerrit_client
async def _fn_project_config(
    cli_args: Args,  # noqa: ARG001 Unused function argument
    gerrit_client: GerritClient,  # noqa: ARG001 Unused function argument
    owners_client: CodeOwnersClient,
) -> None:
    rich_print(await owners_client.project_config())


@with_gerrit_client
async def _fn_component_owners_and_members(
    cli_args: Args,
    gerrit_client: GerritClient,  # noqa: ARG001 Unused function argument
    owners_client: CodeOwnersClient,
) -> None:
    if not cli_args.entities:
        rich_print(yaml.dump(await owners_client.all_components_info()))
        return
    for entity in cli_args.entities:
        rich_print(await owners_client.component_info(entity))


@with_gerrit_client
async def _fn_check_config(
    cli_args: Args,  # noqa: ARG001 Unused function argument
    gerrit_client: GerritClient,  # noqa: ARG001 Unused function argument
    owners_client: CodeOwnersClient,
) -> None:
    await owners_client.check_config()


@with_gerrit_client
async def _fn_all_code_owners_config_files(
    cli_args: Args, gerrit_client: GerritClient, owners_client: CodeOwnersClient
) -> None:
    for owners_file in await owners_client.all_code_owners_config_files():
        owners_file_content = await gerrit_client.repo_file_content(
            owners_file, cli_args.project_name, cli_args.branch
        )
        rich_print(owners_file, len(owners_file_content))


@with_gerrit_client
async def _fn_component_for_path(
    cli_args: Args,
    gerrit_client: GerritClient,  # noqa: ARG001 Unused function argument
    owners_client: CodeOwnersClient,
) -> None:
    for entity in cli_args.entities:
        rich_print(f"[bold]{await owners_client.component_for_path(entity)}[/]")


@with_gerrit_client
async def _fn_component_paths(
    cli_args: Args,
    gerrit_client: GerritClient,  # noqa: ARG001 Unused function argument
    owners_client: CodeOwnersClient,
) -> None:
    for entity in cli_args.entities:
        for path in await owners_client.code_locations(entity):
            rich_print(f"[bold]{path}[/]")


@with_gerrit_client
async def _fn_owners_for(
    cli_args: Args,
    gerrit_client: GerritClient,  # noqa: ARG001 Unused function argument
    owners_client: CodeOwnersClient,
) -> None:
    for entity in cli_args.entities:
        for owner in await owners_client.owners_for(entity):
            rich_print(f"[bold]{owner.get('email')}[/] (account {owner.get('account_id')})")


@with_gerrit_client
async def _fn_stuff(
    cli_args: Args, gerrit_client: GerritClient, owners_client: CodeOwnersClient
) -> None:
    log().debug("check configuration..")
    await owners_client.check_config()
    log().debug("all_code_owners_config_files..")
    for owners_file in await owners_client.all_code_owners_config_files():
        owners_file_content = await gerrit_client.repo_file_content(
            owners_file, cli_args.project_name, cli_args.branch
        )
        rich_print(owners_file, len(owners_file_content))

    log().debug("all_components_info..")
    rich_print(await owners_client.all_components_info())
    rich_print(await owners_client.component_for_path("mixed_component/core_part"))
    rich_print(await owners_client.code_locations("core_component"))
    rich_print(await owners_client.owners_for("mixed_component/core_part"))
    rich_print(await owners_client.component_info("core_component"))


@with_gerrit_client
async def _fn_tui(  # noqa: C901 - too complex
    cli_args: Args, gerrit_client: GerritClient, owners_client: CodeOwnersClient
) -> None:
    class CmkComponents(TuiBaseApp):
        CSS = """
          Header {text-style: bold;}
          Tree > .tree--guides {color: $success-darken-3;}
          Tree > .tree--guides-selected {
            text-style: none;
            color: $success-darken-1;
          }
          #app_log {height: 8;}
        """
        BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
            Binding("ctrl+x", "app.quit", "Quit", show=True),
            Binding("u", "populate_tree"),
        ]

        def __init__(
            self,
            gerrit_client: GerritClient,
            owners_client: CodeOwnersClient,
            branch: str,
        ) -> None:
            super().__init__(logger_show_name=False)
            self.set_log_levels(cli_args.log_level, ("trickkiste", "INFO"))
            self.title = "CMK Components"
            self.main_tree_widget: Tree[None] = Tree("CmkComponents")
            self.main_tree_widget.show_root = False
            self.result_tree_node = self.main_tree_widget.root.add(
                "[bold spring_green1]Search results[/] [white][/]",
                expand=True,
                allow_expand=False,
            )
            self.component_tree_node = self.main_tree_widget.root.add(
                "[bold spring_green1]Components[/] [white](press 'u' to force update)[/]",
                expand=False,
                allow_expand=True,
            )
            self.my_components_tree_node = self.main_tree_widget.root.add(
                "[bold spring_green1]Components I'm member of[/] (coming)",
                expand=False,
                allow_expand=True,
            )
            self.my_files_tree_node = self.main_tree_widget.root.add(
                "[bold spring_green1]Files I'm (co-)responsible for[/] (coming)",
                expand=False,
                allow_expand=True,
            )
            self.gerrit_client = gerrit_client
            self.owners_client = owners_client
            self.branch = branch

        def compose(self) -> ComposeResult:
            """Set up the UI"""
            yield Header(show_clock=True, id="header")
            self.input = Input(placeholder="Type a path", id="dictionary-search")
            yield self.input
            yield self.main_tree_widget
            yield from super().compose()

        async def initialize(self) -> None:
            log().info("initialize auto completion with files and components")
            all_paths = list(
                set(
                    filter(
                        bool,
                        (
                            c
                            for a in map(str.strip, process_output("git ls-files").split("\n"))
                            for b in (a, a.rsplit("/", maxsplit=1)[0])
                            for c in (b, f"/{b}")
                        ),
                    )
                )
            )

            # fixme(frans): store only once
            all_components = list(await owners_client.all_components_info())
            self.input.suggester = SuggestFromList(
                sorted(all_paths + all_components), case_sensitive=False
            )
            self.maintain_statusbar()
            self.action_populate_tree()

        @work(exit_on_error=True)
        async def on_input_changed(self, message: Input.Changed) -> None:
            if message.value:
                self.lookup(message.value)
            else:
                self.result_tree_node.remove_children()

        @work(exclusive=True)
        async def lookup(self, phrase: str) -> None:
            self.result_tree_node.remove_children()
            for o in sorted(await owners_client.owners_for(phrase), key=str):
                self.result_tree_node.add_leaf(f"[cyan]{o.get('email')}[/]")

        @work(exit_on_error=True)
        async def action_populate_tree(self) -> None:
            self.component_tree_node.remove_children()
            for component in await owners_client.all_components_info():
                self.component_tree_node.add_leaf(f"[bold cyan]{component}[/]")

        @work(exit_on_error=True)
        async def maintain_statusbar(self) -> None:
            """Status bar stub (to avoid 'nonsense' status)"""
            while True:
                self.update_status_bar(
                    f"{len(asyncio.all_tasks())} async tasks │ CmkComponents v{__version__}"
                )
                await asyncio.sleep(3)

    await CmkComponents(gerrit_client, owners_client, cli_args.branch).run_async()


def main() -> None:
    """See main docstring"""
    if False:
        for e in sorted(
            set(
                filter(
                    bool,
                    (
                        c
                        for a in map(str.strip, process_output("git ls-files").split("\n"))
                        for b in (a, a.rsplit("/", maxsplit=1)[0])
                        for c in (b, f"/{b}")
                    ),
                )
            )
        ):
            print(e)
        return
    traceback.install()
    cli_args = parse_arguments()
    if cli_args.func != _fn_tui:
        setup_logging(log(), level=cli_args.log_level)
    with suppress(KeyboardInterrupt):
        asyncio.run(cli_args.func(cli_args))


def log() -> logging.Logger:
    """Convenience function retrieves 'our' logger"""
    return logging.getLogger("trickkiste.cmk-components")


if __name__ == "__main__":
    main()
