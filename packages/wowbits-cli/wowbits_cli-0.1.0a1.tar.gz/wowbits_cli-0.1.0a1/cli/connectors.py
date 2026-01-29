#!/usr/bin/env python3
"""
WowBits CLI - Connectors Command

Handles connector management including listing, creating, updating, and deleting connectors.
Supports interactive mode for creating connectors with provider-specific configuration.
"""

import argparse
import getpass
import json
import sys
import uuid
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.schema import Connector, ConnectorStatus
from pylibs.database_manager import get_session_context


def load_providers() -> Dict[str, Any]:
    """Load provider definitions from JSON file."""
    providers_file = Path(__file__).parent / "data" / "providers.json"
    try:
        with open(providers_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: providers.json not found at {providers_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in providers.json: {e}")
        sys.exit(1)


AVAILABLE_PROVIDERS = load_providers()


def print_providers() -> None:
    """Print available providers."""
    print("\n  AVAILABLE PROVIDERS")
    
    for provider_id, provider in AVAILABLE_PROVIDERS.items():
        print(f"    {provider_id:<15} {provider['description']}")
    
    print()


def prompt_for_value(field_name: str, field_config: Dict[str, Any]) -> str:
    """Prompt user for a config value, masking secrets."""
    is_secret = field_config.get("is_secret", False)
    required = field_config.get("required", True)
    
    label = f"  {field_name} (input hidden) " + ": "
    
    if is_secret:
        return getpass.getpass(label).strip()
    return input(label).strip()


def interactive_create_connector() -> Optional[Dict[str, Any]]:
    """Interactively create a connector."""
    print("\n  Create Connector")
    
    # Provider selection first
    provider_list = list(AVAILABLE_PROVIDERS.keys())
    print("\n  Available Providers:")
    for i, pid in enumerate(provider_list, 1):
        pinfo = AVAILABLE_PROVIDERS[pid]
        print(f"    {i:2}. {pid:<15} {pinfo['name']}")
    
    provider_input = input("\n  Provider (number or name): ").strip()
    
    if provider_input.isdigit():
        idx = int(provider_input) - 1
        if not (0 <= idx < len(provider_list)):
            print(f"  Error: Choose 1-{len(provider_list)}")
            return None
        provider = provider_list[idx]
    elif provider_input.lower() in AVAILABLE_PROVIDERS:
        provider = provider_input.lower()
    else:
        print(f"  Error: Unknown provider '{provider_input}'")
        return None
    
    provider_info = AVAILABLE_PROVIDERS[provider]
    
    # Use provider name as connector name
    name = provider_info['name']
    print(f"\n  Connector name: {name}")
    
    # Config
    config_schema = provider_info.get("config_schema", {})
    config = {}
    
    if config_schema:
        for field_name, field_config in config_schema.items():
            value = prompt_for_value(field_name, field_config)
            if value:
                config[field_name] = value
            elif field_config.get("required", True):
                print(f"  Error: {field_name} is required")
                return None
    else:
        config_json = input("\n  Config JSON: ").strip()
        if config_json:
            try:
                config = json.loads(config_json)
            except json.JSONDecodeError as e:
                print(f"  Error: Invalid JSON - {e}")
                return None
    
    # Confirm
    confirm = input("\n  Confirm? [Y/n]: ").strip().lower()
    if confirm and confirm not in ['y', 'yes', '']:
        print("  Cancelled")
        return None
    
    return {"name": name, "provider": provider, "config": config, "status": "ACTIVE"}


def interactive_create_with_provider(provider: str, status: str) -> Optional[Dict[str, Any]]:
    """Create connector with pre-selected provider."""
    provider_info = AVAILABLE_PROVIDERS.get(provider)
    if not provider_info:
        print(f"  Error: Unknown provider '{provider}'")
        return None
    
    # Use provider name as connector name
    name = provider_info['name']
    
    print(f"\n  Create {name} Connector")
    print("  " + "-" * 30 + "\n")
    
    config_schema = provider_info.get("config_schema", {})
    config = {}
    
    if config_schema:
        print("  Configuration (* required, secrets masked):")
        for field_name, field_config in config_schema.items():
            value = prompt_for_value(field_name, field_config)
            if value:
                config[field_name] = value
            elif field_config.get("required", True):
                print(f"  Error: {field_name} is required")
                return None
    
    confirm = input("\n  Confirm? [Y/n]: ").strip().lower()
    if confirm and confirm not in ['y', 'yes', '']:
        print("  Cancelled")
        return None
    
    return {"name": name, "provider": provider, "config": config, "status": status}


class ConnectorManager:
    """Manager class for connector CRUD operations."""
    
    def list_connectors(self) -> List[Dict[str, Any]]:
        """List all connectors."""
        with get_session_context() as session:
            connectors = session.query(Connector).order_by(Connector.created_at.desc()).all()
            return [self._connector_to_dict(c) for c in connectors]
    
    def get_connector(self, name: str) -> Optional[Dict[str, Any]]:
        """Get connector by name."""
        with get_session_context() as session:
            connector = session.query(Connector).filter(Connector.name == name).first()
            return self._connector_to_dict(connector) if connector else None

    def create_connector(
        self,
        name: str,
        provider: str,
        config: Optional[Dict[str, Any]] = None,
        status: str = "ACTIVE"
    ) -> Dict[str, Any]:
        """Create a new connector."""
        with get_session_context() as session:
            existing = session.query(Connector).filter(Connector.name == name).first()
            if existing:
                raise ValueError(f"Connector '{name}' already exists")
            
            connector = Connector(
                name=name,
                provider=provider,
                config=config or {},
                status=ConnectorStatus[status]
            )
            session.add(connector)
            session.flush()
            return self._connector_to_dict(connector)

    def update_connector(
        self,
        connector_id: str,
        name: Optional[str] = None,
        provider: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing connector by ID."""
        try:
            parsed_id = uuid.UUID(connector_id)
        except ValueError:
            raise ValueError(f"Invalid ID format: '{connector_id}'")
        
        with get_session_context() as session:
            connector = session.query(Connector).filter(Connector.id == parsed_id).first()
            if not connector:
                return None
            
            if name and name != connector.name:
                if session.query(Connector).filter(Connector.name == name).first():
                    raise ValueError(f"Connector '{name}' already exists")
                connector.name = name
            
            if provider:
                connector.provider = provider
            if config is not None:
                connector.config = config
            if status:
                connector.status = ConnectorStatus[status]
            
            connector.updated_at = datetime.now(timezone.utc)
            return self._connector_to_dict(connector)

    def delete_connector(self, connector_id: str) -> bool:
        """Delete connector by ID."""
        try:
            parsed_id = uuid.UUID(connector_id)
        except ValueError:
            raise ValueError(f"Invalid ID format: '{connector_id}'")
        
        with get_session_context() as session:
            connector = session.query(Connector).filter(Connector.id == parsed_id).first()
            if not connector:
                return False
            session.delete(connector)
            return True

    def delete_connector_by_name(self, name: str) -> Optional[str]:
        """Delete connector by name. Returns the deleted connector's ID or None if not found."""
        with get_session_context() as session:
            connector = session.query(Connector).filter(Connector.name == name).first()
            if not connector:
                return None
            connector_id = str(connector.id)
            session.delete(connector)
            return connector_id

    def _connector_to_dict(self, connector: Connector) -> Dict[str, Any]:
        """Convert connector model to dictionary."""
        return {
            "id": str(connector.id),
            "name": connector.name,
            "provider": connector.provider,
            "config": connector.config or {},
            "status": connector.status.value if connector.status else "ACTIVE",
            "created_at": connector.created_at.isoformat() if connector.created_at else None,
            "updated_at": connector.updated_at.isoformat() if connector.updated_at else None
        }


def mask_sensitive_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive values in config."""
    sensitive_keys = ['api_key', 'access_token', 'secret', 'password', 'token', 'signing_secret', 'bot_token']
    masked = {}
    for key, value in config.items():
        if any(sk in key.lower() for sk in sensitive_keys) and isinstance(value, str) and len(value) > 8:
            masked[key] = value[:4] + '*' * (len(value) - 8) + value[-4:]
        else:
            masked[key] = value
    return masked


# ============ Helper Functions for Connector Config Access ============

def get_connector_config(connector_name: str) -> Optional[Dict[str, Any]]:
    """Get connector config by name. Returns None if not found.
    
    Usage:
        config = get_connector_config("OpenAI")
        api_key = config.get("api_key") if config else None
    """
    try:
        manager = ConnectorManager()
        connector = manager.get_connector(connector_name)
        return connector.get("config") if connector else None
    except Exception:
        return None


def get_api_key(connector_name: str) -> Optional[str]:
    """Get API key from a connector's config.
    
    Usage:
        openai_key = get_api_key("OpenAI")
        google_key = get_api_key("Google AI")
    """
    config = get_connector_config(connector_name)
    if not config:
        return None
    # Try common key names
    return config.get("api_key") or config.get("apiKey") or config.get("key")


def print_connector(connector: Dict[str, Any]) -> None:
    """Print connector details."""
    masked = mask_sensitive_config(connector.get('config', {}))
    print(f"\n  ID:       {connector['id']}")
    print(f"  Name:     {connector['name']}")
    print(f"  Provider: {connector['provider']}")
    print(f"  Status:   {connector['status']}")
    print(f"  Config:   {json.dumps(masked)}")
    print(f"  Created:  {connector['created_at']}")
    print(f"  Updated:  {connector['updated_at']}\n")


def print_connectors_table(connectors: List[Dict[str, Any]]) -> None:
    """Print connectors table."""
    if not connectors:
        print("\n  No connectors found.\n")
        return
    
    print(f"\n  {'ID':<36}  {'Name':<20}  {'Provider':<12}  {'Status':<10}")
    print("  " + "-" * 82)
    
    for c in connectors:
        name = c['name'][:18] + '..' if len(c['name']) > 20 else c['name']
        print(f"  {c['id']:<36}  {name:<20}  {c['provider']:<12}  {c.get('status', 'ACTIVE'):<10}")
    
    print(f"\n  Total: {len(connectors)}\n")


# ============ Simple Interface Functions for wowbits.py ============

def list_connectors() -> None:
    """List all connectors (simple interface)."""
    manager = ConnectorManager()
    print_connectors_table(manager.list_connectors())


def create_connector(provider: Optional[str] = None, config: Optional[str] = None, interactive: bool = True) -> None:
    """Create a new connector (simple interface)."""
    manager = ConnectorManager()
    
    if interactive and not config:
        # Interactive mode
        if provider:
            connector_data = interactive_create_with_provider(provider, "ACTIVE")
        else:
            connector_data = interactive_create_connector()
        
        if not connector_data:
            sys.exit(1)
        
        connector = manager.create_connector(**connector_data)
    else:
        # Non-interactive mode
        if not provider:
            print("  Error: --provider is required in non-interactive mode")
            sys.exit(1)
        
        config_dict = {}
        if config:
            try:
                config_dict = json.loads(config)
            except json.JSONDecodeError as e:
                print(f"  Error: Invalid JSON - {e}")
                sys.exit(1)
        
        provider_info = AVAILABLE_PROVIDERS.get(provider)
        name = provider_info['name'] if provider_info else provider
        
        connector = manager.create_connector(
            name=name,
            provider=provider,
            config=config_dict,
            status="ACTIVE"
        )
    
    print("\n  ✅ Connector created successfully!\n")


def update_connector(name: str, config: str) -> None:
    """Update an existing connector by name (simple interface)."""
    manager = ConnectorManager()
    
    # First get the connector to find its ID
    connector = manager.get_connector(name)
    if not connector:
        print(f"  Error: Connector '{name}' not found")
        sys.exit(1)
    
    try:
        config_dict = json.loads(config)
    except json.JSONDecodeError as e:
        print(f"  Error: Invalid JSON - {e}")
        sys.exit(1)
    
    updated = manager.update_connector(
        connector_id=connector['id'],
        config=config_dict
    )
    
    if updated:
        print("\n  ✅ Connector updated successfully!")
        print_connector(updated)
    else:
        print(f"  Error: Failed to update connector")
        sys.exit(1)


def delete_connector(name: str) -> None:
    """Delete a connector by name (simple interface)."""
    manager = ConnectorManager()
    
    deleted_id = manager.delete_connector_by_name(name)
    if deleted_id:
        print(f"\n  ✅ Connector '{name}' deleted (ID: {deleted_id})\n")
    else:
        print(f"  Error: Connector not found with name: {name}")
        sys.exit(1)


# ============ Full Command Handler ============

def handle_connector_command(action: str, obj: str, args: List[str]) -> None:
    """Handle connector commands with full argument parsing."""
    manager = ConnectorManager()
    
    try:
        if action == "list" and obj == "providers":
            print_providers()
            return
        
        if action == "list" and obj == "connector":
            print_connectors_table(manager.list_connectors())
            return
        
        parser = argparse.ArgumentParser(prog=f"wowbits {action} connector")
        
        if action == "create":
            parser.add_argument("--provider", "-p", type=str, choices=list(AVAILABLE_PROVIDERS.keys()))
            parser.add_argument("--config", type=str)
            parser.add_argument("--status", "-s", type=str, choices=["ACTIVE", "INACTIVE"], default="ACTIVE")
            parser.add_argument("--interactive", "-i", action="store_true")
        
        elif action == "update":
            parser.add_argument("--id", type=str, required=True)
            parser.add_argument("--name", "-n", type=str)
            parser.add_argument("--provider", "-p", type=str, choices=list(AVAILABLE_PROVIDERS.keys()))
            parser.add_argument("--config", type=str)
            parser.add_argument("--status", "-s", type=str, choices=["ACTIVE", "INACTIVE"])
        
        elif action == "delete":
            parser.add_argument("--id", type=str, help="Connector ID (UUID)")
            parser.add_argument("--name", "-n", type=str, help="Connector name")
        
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
        
        parsed_args = parser.parse_args(args)
        
        if action == "create":
            use_interactive = (
                parsed_args.interactive or 
                (not parsed_args.provider and not parsed_args.config) or
                (parsed_args.provider and not parsed_args.config)
            )
            
            if use_interactive:
                if not parsed_args.provider:
                    connector_data = interactive_create_connector()
                else:
                    connector_data = interactive_create_with_provider(
                        parsed_args.provider, parsed_args.status
                    )
                if not connector_data:
                    sys.exit(1)
                connector = manager.create_connector(**connector_data)
            else:
                config = json.loads(parsed_args.config) if parsed_args.config else None
                # Use provider name as connector name
                provider_info = AVAILABLE_PROVIDERS.get(parsed_args.provider)
                name = provider_info['name'] if provider_info else parsed_args.provider
                connector = manager.create_connector(
                    name=name,
                    provider=parsed_args.provider,
                    config=config,
                    status=parsed_args.status
                )
            
            print("\n  Connector created successfully!\n")
        
        elif action == "update":
            config = json.loads(parsed_args.config) if parsed_args.config else None
            connector = manager.update_connector(
                connector_id=parsed_args.id,
                name=parsed_args.name,
                provider=parsed_args.provider,
                config=config,
                status=parsed_args.status
            )
            if connector:
                print("\n  Connector updated successfully!")
                print_connector(connector)
            else:
                print(f"  Error: Connector not found")
                sys.exit(1)
        
        elif action == "delete":
            # Require at least --id or --name
            if not parsed_args.id and not parsed_args.name:
                print("  Error: Either --id or --name is required")
                print("  Usage: wowbits delete connector --id <uuid>")
                print("         wowbits delete connector --name <name>")
                sys.exit(1)
            
            if parsed_args.id:
                if manager.delete_connector(parsed_args.id):
                    print(f"\n  ✅ Connector deleted (ID: {parsed_args.id})\n")
                else:
                    print(f"  Error: Connector not found with ID: {parsed_args.id}")
                    sys.exit(1)
            else:
                deleted_id = manager.delete_connector_by_name(parsed_args.name)
                if deleted_id:
                    print(f"\n  ✅ Connector '{parsed_args.name}' deleted (ID: {deleted_id})\n")
                else:
                    print(f"  Error: Connector not found with name: {parsed_args.name}")
                    sys.exit(1)
    
    except json.JSONDecodeError as e:
        print(f"  Error: Invalid JSON - {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"  Error: {e}")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)


def main():
    """Main entry point for standalone execution."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nRun: wowbits --help")
        sys.exit(0)
    
    if sys.argv[1].startswith("--"):
        flag = sys.argv[1][2:]
        remaining = sys.argv[2:]
        
        commands = {
            "list": ("list", "connector"),
            "providers": ("list", "providers"),
            "create": ("create", "connector"),
            "update": ("update", "connector"),
            "delete": ("delete", "connector")
        }
        
        if flag in commands:
            handle_connector_command(commands[flag][0], commands[flag][1], remaining)
        else:
            print(f"Unknown flag: --{flag}")
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(0)


if __name__ == "__main__":
    main()

