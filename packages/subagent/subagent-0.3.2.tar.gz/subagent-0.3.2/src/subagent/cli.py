"""Main CLI entry point for subagent."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the subagent CLI."""
    parser = argparse.ArgumentParser(
        prog="subagent",
        description="Manage workspace agents across different backends",
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=True,
    )
    
    # Add the 'code' subcommand for VS Code workspace agents
    code_parser = subparsers.add_parser(
        "code",
        help="Manage VS Code workspace agents",
    )
    code_subparsers = code_parser.add_subparsers(
        dest="action",
        help="VS Code agent actions",
        required=True,
    )
    
    # Add 'code-insiders' subcommand for VS Code Insiders workspace agents
    code_insiders_parser = subparsers.add_parser(
        "code-insiders",
        help="Manage VS Code Insiders workspace agents",
    )
    code_insiders_subparsers = code_insiders_parser.add_subparsers(
        dest="action",
        help="VS Code Insiders agent actions",
        required=True,
    )
    
    # Add 'code provision' subcommand
    from .vscode.cli import add_provision_parser, add_chat_parser, add_warmup_parser, add_list_parser, add_unlock_parser
    add_provision_parser(code_subparsers)
    add_chat_parser(code_subparsers)
    add_warmup_parser(code_subparsers)
    add_list_parser(code_subparsers)
    add_unlock_parser(code_subparsers)
    
    # Add 'code-insiders provision' subcommand
    add_provision_parser(code_insiders_subparsers)
    add_chat_parser(code_insiders_subparsers)
    add_warmup_parser(code_insiders_subparsers)
    add_list_parser(code_insiders_subparsers)
    add_unlock_parser(code_insiders_subparsers)
    
    args = parser.parse_args(argv)
    
    # Determine which VS Code executable to use
    vscode_cmd = "code-insiders" if args.command == "code-insiders" else "code"
    args.vscode_cmd = vscode_cmd
    
    # Route to the appropriate handler
    if args.command in ["code", "code-insiders"]:
        if args.action == "provision":
            from .vscode.cli import handle_provision
            return handle_provision(args)
        elif args.action == "chat":
            from .vscode.cli import handle_chat
            return handle_chat(args)
        elif args.action == "warmup":
            from .vscode.cli import handle_warmup
            return handle_warmup(args)
        elif args.action == "list":
            from .vscode.cli import handle_list
            return handle_list(args)
        elif args.action == "unlock":
            from .vscode.cli import handle_unlock
            return handle_unlock(args)
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
