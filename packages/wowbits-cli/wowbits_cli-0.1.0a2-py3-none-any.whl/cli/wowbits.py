#!/usr/bin/env python3
"""
WowBits AI Platform CLI

A command-line interface for building and running WowBits agents.

Command structure: wowbits <action> <resource> [args]
Examples:
    wowbits list functions
    wowbits create functions
    wowbits list connectors
    wowbits create connector --provider openai --config '{...}'
"""

import argparse
import sys
import os
import re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_env_file_from_root() -> None:
    """Load additional environment variables from WOWBITS_ROOT_DIR/.env file."""
    root_dir = os.environ.get('WOWBITS_ROOT_DIR')
    if not root_dir:
        return
    
    env_file = Path(root_dir) / ".env"
    if env_file.exists():
        _load_env_file(env_file)


def _try_load_from_home_env() -> None:
    """Try to load WOWBITS_ROOT_DIR from ~/.wowbits/.env or similar locations."""
    home_dir = Path.home()
    
    # Check common locations
    possible_locations = [
        home_dir / "wowbits" / ".env",
        home_dir / ".wowbits" / ".env",
    ]
    
    for env_file in possible_locations:
        if env_file.exists():
            _load_env_file(env_file)
            if os.environ.get('WOWBITS_ROOT_DIR'):
                return


def _load_env_file(env_file: Path) -> None:
    """Load environment variables from a .env file."""
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=value format
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass


def load_wowbits_env() -> None:
    """
    Load WOWBITS_ROOT_DIR environment variable from shell config files.
    
    This function ensures the environment variable is available even if the user
    hasn't sourced their shell config in the current terminal session.
    
    Priority:
    1. If already set in environment, use that
    2. Try to load from shell config files (.zshrc, .bashrc, .bash_profile)
    3. Try to load from .env file in WOWBITS_ROOT_DIR or home directory
    """
    # If already set, nothing to do
    if os.environ.get('WOWBITS_ROOT_DIR'):
        # Also load the .env file from root dir if it exists
        _load_env_file_from_root()
        return
    
    home_dir = Path.home()
    
    # Determine shell config files to check based on current shell
    shell = os.environ.get('SHELL', '/bin/bash')
    
    if 'zsh' in shell:
        config_files = [home_dir / ".zshrc"]
    elif 'bash' in shell:
        config_files = [home_dir / ".bashrc", home_dir / ".bash_profile"]
    else:
        # Check all common config files
        config_files = [
            home_dir / ".zshrc",
            home_dir / ".bashrc",
            home_dir / ".bash_profile"
        ]
    
    # Pattern to match: export WOWBITS_ROOT_DIR="value" or export WOWBITS_ROOT_DIR='value' or export WOWBITS_ROOT_DIR=value
    pattern = re.compile(r'^export\s+WOWBITS_ROOT_DIR=(["\']?)(.+?)\1\s*$')
    
    for config_file in config_files:
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        match = pattern.match(line.strip())
                        if match:
                            root_dir = match.group(2)
                            # Expand any ~ or environment variables in the path
                            root_dir = os.path.expanduser(root_dir)
                            root_dir = os.path.expandvars(root_dir)
                            os.environ['WOWBITS_ROOT_DIR'] = root_dir
                            # Load additional env vars from .env file
                            _load_env_file_from_root()
                            return
            except Exception:
                continue
    
    # If still not found, check for .env file in home directory
    _try_load_from_home_env()


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="wowbits",
        description="WowBits AI Platform CLI - Build and run AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="WowBits CLI v0.1.0"
    )
    
    subparsers = parser.add_subparsers(dest="action", help="Available actions")
    
    # Setup command (standalone, no resource needed)
    setup_parser = subparsers.add_parser(
        "setup",
        help="Setup database, environment, and initialize data"
    )
    setup_parser.add_argument(
        "--root-dir",
        help="Root directory for WowBits (default: ~/wowbits)",
        default=None
    )
    
    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List resources (functions, connectors, agents)"
    )
    list_subparsers = list_parser.add_subparsers(dest="resource", help="Resource to list")
    
    # list functions
    list_subparsers.add_parser("functions", help="List all Python functions")
    
    # list connectors
    list_subparsers.add_parser("connectors", help="List all connectors")
    
    # list agents
    list_subparsers.add_parser("agents", help="List all agents")
    
    # Create command
    create_parser = subparsers.add_parser(
        "create",
        help="Create resources (functions, agent, connector)"
    )
    create_subparsers = create_parser.add_subparsers(dest="resource", help="Resource to create")
    
    # create functions
    create_functions = create_subparsers.add_parser("functions", help="Create/sync Python functions from WOWBITS_ROOT_DIR/functions")
    create_functions.add_argument(
        "--dir",
        help="Custom functions directory (default: WOWBITS_ROOT_DIR/functions)",
        default=None
    )
    
    # create connectors
    create_connector = create_subparsers.add_parser("connector", help="Create a new connector")
    create_connector.add_argument("--provider", "-p", help="Provider name (e.g., openai, anthropic)")
    create_connector.add_argument("--config", help="JSON configuration string (interactive mode if not provided)")
    
    # create agent
    create_agent = create_subparsers.add_parser("agent", help="Create agent from YAML configuration")
    create_agent.add_argument("name", help="Agent name (looks for WOWBITS_ROOT_DIR/agent_studio/<name>.yaml)")
    create_agent.add_argument("-c", "--config", help="Custom path to YAML configuration file (optional)")
    
    # Update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update resources (connectors, agents)"
    )
    update_subparsers = update_parser.add_subparsers(dest="resource", help="Resource to update")
    
    # update connectors
    update_connectors = update_subparsers.add_parser("connectors", help="Update an existing connector")
    update_connectors.add_argument("name", help="Connector name or ID")
    update_connectors.add_argument("--config", required=True, help="JSON configuration string")
    
    # Delete command
    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete resources (connectors, agents)"
    )
    delete_subparsers = delete_parser.add_subparsers(dest="resource", help="Resource to delete")
    
    # delete connectors
    delete_connectors = delete_subparsers.add_parser("connectors", help="Delete a connector")
    delete_connectors.add_argument("name", help="Connector name or ID")
    
    # Run command (for agents)
    run_parser = subparsers.add_parser(
        "run",
        help="Run resources (agents)"
    )
    run_subparsers = run_parser.add_subparsers(dest="resource", help="Resource to run")
    
    # run agent - creates agent.py file from database
    run_agent = run_subparsers.add_parser("agent", help="Create agent.py file from database")
    run_agent.add_argument("name", help="Agent name")
    
    return parser


def handle_setup_command(args):
    """Handle setup command."""
    from cli.setup import run_setup, setup_root_directory
    
    # First setup root directory
    root_path = setup_root_directory(args.root_dir)
    
    # Then run the rest of setup, passing the root path for database configuration
    run_setup(root_path=root_path)


def handle_list(args):
    """Handle list command."""
    if args.resource == "functions":
        from cli.functions import list_functions
        list_functions()
    elif args.resource == "connectors":
        from cli.connectors import list_connectors
        list_connectors()
    elif args.resource == "agents":
        from cli.agents import list_agents
        list_agents()
    else:
        print(f"❌ Unknown resource: {args.resource}")
        print("   Available resources: functions, connectors, agents")
        sys.exit(1)


def handle_create(args):
    """Handle create command."""
    if args.resource == "functions":
        from cli.functions import scan_and_create_functions, get_functions_dir
        
        if args.dir:
            functions_dir = Path(args.dir).expanduser().resolve()
        else:
            functions_dir = get_functions_dir()
        
        if functions_dir:
            scan_and_create_functions(functions_dir)
    elif args.resource == "connector":
        from cli.connectors import create_connector
        # Use interactive mode if no config provided
        create_connector(args.provider, args.config, interactive=not args.config)
    elif args.resource == "agent":
        from cli.agents import create_agent
        create_agent(args.name, args.config)
    else:
        print(f"❌ Unknown resource: {args.resource}")
        print("   Available resources: functions, connector, agent")
        sys.exit(1)


def handle_update(args):
    """Handle update command."""
    if args.resource == "connectors":
        from cli.connectors import update_connector
        update_connector(args.name, args.config)
    else:
        print(f"❌ Unknown resource: {args.resource}")
        print("   Available resources: connectors")
        sys.exit(1)


def handle_delete(args):
    """Handle delete command."""
    if args.resource == "connectors":
        from cli.connectors import delete_connector
        delete_connector(args.name)
    else:
        print(f"❌ Unknown resource: {args.resource}")
        print("   Available resources: connectors")
        sys.exit(1)


def handle_run(args):
    """Handle run command."""
    if args.resource == "agent":
        from cli.agents import run_agent
        run_agent(args.name)
    else:
        print(f"❌ Unknown resource: {args.resource}")
        print("   Available resources: agent")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    # Load WOWBITS_ROOT_DIR and other env vars from shell config/env files
    # Skip for setup command as it will configure these
    if len(sys.argv) < 2 or sys.argv[1] != "setup":
        load_wowbits_env()
    
    parser = create_parser()
    
    # If no arguments provided, print help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    args = parser.parse_args()
    
    try:
        if args.action == "setup":
            handle_setup_command(args)
        elif args.action == "list":
            if not args.resource:
                parser.parse_args(["list", "--help"])
            handle_list(args)
        elif args.action == "create":
            if not args.resource:
                parser.parse_args(["create", "--help"])
            handle_create(args)
        elif args.action == "update":
            if not args.resource:
                parser.parse_args(["update", "--help"])
            handle_update(args)
        elif args.action == "delete":
            if not args.resource:
                parser.parse_args(["delete", "--help"])
            handle_delete(args)
        elif args.action == "run":
            if not args.resource:
                parser.parse_args(["run", "--help"])
            handle_run(args)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
