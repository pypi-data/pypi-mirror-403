#!/usr/bin/env python3
"""
WowBits CLI - Setup Command

Handles initial setup including database configuration and data initialization.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylibs.database_manager import get_session_context
from db.schema import Agent, Skill, Tool, Connector, MCPConfig
from cli.functions import scan_and_create_functions


def setup_root_directory(root_dir: Optional[str] = None) -> Path:
    """
    Setup the WowBits root directory and required subdirectories.
    
    Args:
        root_dir: Optional root directory path. If None, uses ~/wowbits
        
    Returns:
        Path: The root directory path
    """
    # Determine root directory
    if root_dir:
        root_path = Path(root_dir).expanduser().resolve()
    else:
        # Ask user for root directory
        default_root = Path.home() / "wowbits"
        print(f"\n📁 WowBits Root Directory Setup")
        print(f"   Default: {default_root}")
        user_input = input(f"   Enter root directory path (press Enter for default): ").strip()
        
        if user_input:
            root_path = Path(user_input).expanduser().resolve()
        else:
            root_path = default_root
    
    # Create root directory if it doesn't exist
    if not root_path.exists():
        print(f"   Creating root directory: {root_path}")
        root_path.mkdir(parents=True, exist_ok=True)
    else:
        print(f"   Using existing root directory: {root_path}")
    
    # Create required subdirectories
    subdirs = ["data", "agent_studio", "functions", "agent_runner"]
    for subdir in subdirs:
        subdir_path = root_path / subdir
        if not subdir_path.exists():
            print(f"   Creating {subdir} directory: {subdir_path}")
            subdir_path.mkdir(parents=True, exist_ok=True)
        else:
            print(f"   {subdir} directory already exists: {subdir_path}")
    
    # Create __init__.py in agent_runner directory for ADK web compatibility
    agent_runner_init = root_path / "agent_runner" / "__init__.py"
    if not agent_runner_init.exists():
        agent_runner_init.write_text("# WowBits Agent Runner Directory\n")
        print(f"   Created agent_runner __init__.py: {agent_runner_init}")
    
    # Set WOWBITS_ROOT_DIR environment variable
    os.environ["WOWBITS_ROOT_DIR"] = str(root_path)
    
    # Persist WOWBITS_ROOT_DIR to shell configuration file (bashrc/zshrc)
    _persist_env_to_shell_config("WOWBITS_ROOT_DIR", str(root_path))
    
    # Update .env file if it exists, or create one
    env_file = Path.cwd() / ".env"
    env_lines = []
    wowbits_root_found = False
    
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("WOWBITS_ROOT_DIR="):
                    env_lines.append(f"WOWBITS_ROOT_DIR={root_path}\n")
                    wowbits_root_found = True
                else:
                    env_lines.append(line)
    
    if not wowbits_root_found:
        env_lines.append(f"WOWBITS_ROOT_DIR={root_path}\n")
    
    with open(env_file, "w") as f:
        f.writelines(env_lines)
    
    print(f"\n✅ Root directory setup complete!")
    print(f"   WOWBITS_ROOT_DIR={root_path}")
    print(f"   Environment variable saved to .env file\n")
    
    return root_path


def _persist_env_to_shell_config(var_name: str, var_value: str) -> None:
    """
    Persist an environment variable to the user's shell configuration file.
    
    Detects the user's shell and adds/updates the export statement in the
    appropriate config file (.bashrc or .zshrc).
    
    Args:
        var_name: The environment variable name
        var_value: The environment variable value
    """
    home_dir = Path.home()
    
    # Determine which shell config file to use
    shell = os.environ.get('SHELL', '/bin/bash')
    
    if 'zsh' in shell:
        shell_config_files = [home_dir / ".zshrc"]
        shell_name = "zsh"
    elif 'bash' in shell:
        # For bash, prefer .bashrc but also check .bash_profile on macOS
        shell_config_files = [home_dir / ".bashrc"]
        if sys.platform == 'darwin':
            # On macOS, .bash_profile is often used for login shells
            bash_profile = home_dir / ".bash_profile"
            if bash_profile.exists() and not (home_dir / ".bashrc").exists():
                shell_config_files = [bash_profile]
        shell_name = "bash"
    else:
        # Default to both for unknown shells
        shell_config_files = [home_dir / ".bashrc", home_dir / ".zshrc"]
        shell_name = "bash/zsh"
    
    export_line = f'export {var_name}="{var_value}"'
    export_pattern = f'export {var_name}='
    
    for config_file in shell_config_files:
        try:
            # Read existing content
            existing_lines = []
            var_found = False
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.strip().startswith(export_pattern):
                            # Replace existing export line
                            existing_lines.append(f'{export_line}\n')
                            var_found = True
                        else:
                            existing_lines.append(line)
            
            # If variable not found, append it
            if not var_found:
                # Add a newline before if file doesn't end with one
                if existing_lines and not existing_lines[-1].endswith('\n'):
                    existing_lines.append('\n')
                # Add a comment and the export
                existing_lines.append(f'\n# WowBits CLI environment variable\n')
                existing_lines.append(f'{export_line}\n')
            
            # Write back to config file
            with open(config_file, 'w') as f:
                f.writelines(existing_lines)
            
            print(f"   ✅ {var_name} added to {config_file}")
            print(f"   💡 Run 'source {config_file}' or open a new terminal to apply changes")
            
        except PermissionError:
            print(f"   ⚠️  Could not write to {config_file}: Permission denied")
        except Exception as e:
            print(f"   ⚠️  Could not update {config_file}: {e}")


def get_db_connection_string(root_path: Optional[Path] = None) -> str:
    """Prompt user for database connection string or SQLite option.
    
    Args:
        root_path: Optional root directory path. If provided, SQLite database
                   will be automatically created in root_path/data/wowbits.db
    """
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║               Database Configuration                          ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    print("Choose your database option:")
    print("  1. SQLite (local file database - recommended for development)")
    print("  2. Cloud Database (PostgreSQL/MySQL/etc.)\n")
    
    choice = input("Enter your choice (1-2): ").strip()
    
    if choice == "1":
        # SQLite option - use root_path/data if available
        if root_path:
            db_path = root_path / "data" / "wowbits.db"
            print(f"\n📁 SQLite database will be created at: {db_path}")
        else:
            # Fallback if root_path not provided
            src_dir = Path(__file__).parent.parent
            default_db_dir = src_dir.parent / "data"
            db_path = default_db_dir / "wowbits.db"
            print(f"\n📁 SQLite database will be created at: {db_path}")
        
        # Check if the directory exists or can be created
        db_dir = db_path.parent
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Database directory verified: {db_dir}")
        except Exception as e:
            print(f"❌ Error: Cannot create database directory at {db_dir}")
            print(f"   Reason: {e}")
            sys.exit(1)
        
        # Check if we have write permissions
        if not os.access(db_dir, os.W_OK):
            print(f"❌ Error: No write permission for directory: {db_dir}")
            sys.exit(1)
        
        db_url = f"sqlite:///{db_path}"
        print(f"✅ Using SQLite database at: {db_path}")
        return db_url
        
    elif choice == "2":
        # Cloud Database option
        print("\nCloud Database Configuration:")
        print("Please provide your database connection string.")
        print("\nExamples:")
        print("  PostgreSQL: postgresql://user:password@host:5432/database")
        print("  MySQL: mysql://user:password@host:3306/database")
        print("  Other: <dialect>://<user>:<password>@<host>:<port>/<database>\n")
        
        db_url = input("Database Connection String: ").strip()
        
        if not db_url:
            print("❌ Error: Database connection string cannot be empty")
            sys.exit(1)
        
        # Validate connection string format
        if "://" not in db_url:
            print("❌ Error: Invalid connection string format")
            print("   Expected format: <dialect>://<user>:<password>@<host>:<port>/<database>")
            sys.exit(1)
        
        # Test the connection
        print("\n🔍 Testing database connection...")
        try:
            from sqlalchemy import create_engine
            engine = create_engine(db_url)
            
            # Try to connect
            with engine.connect() as conn:
                print("✅ Database connection successful")
            
            engine.dispose()
            return db_url
            
        except Exception as e:
            print(f"❌ Error: Failed to connect to database")
            print(f"   Reason: {e}")
            print("\n   Please verify:")
            print("   • Connection string is correct")
            print("   • Database server is running")
            print("   • Network connectivity is available")
            print("   • Credentials are valid")
            sys.exit(1)
        
    else:
        print("❌ Error: Invalid choice. Please select 1 or 2.")
        sys.exit(1)


def create_database_tables(db_url: str) -> None:
    """Create database tables if they don't exist."""
    from sqlalchemy import create_engine
    from db.schema import Base
    
    print("\n📦 Creating database tables...")
    
    try:
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully")
        engine.dispose()
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


def load_yaml_files(data_dir: Path) -> List[Dict[str, Any]]:
    """Load all YAML files from the data directory."""
    if not data_dir.exists():
        print(f"⚠️  Data directory not found: {data_dir}")
        return []
    
    yaml_files = list(data_dir.glob("*.yaml")) + list(data_dir.glob("*.yml"))
    
    if not yaml_files:
        print(f"⚠️  No YAML files found in: {data_dir}")
        return []
    
    all_objects = []
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
                
                if isinstance(data, list):
                    all_objects.extend(data)
                elif isinstance(data, dict):
                    all_objects.append(data)
                    
            print(f"✅ Loaded: {yaml_file.name}")
        except Exception as e:
            print(f"❌ Error loading {yaml_file.name}: {e}")
    
    return all_objects


def create_object_from_yaml(session, obj_data: Dict[str, Any]) -> None:
    """Create database object based on kind field."""
    kind = obj_data.get('kind', '').lower()
    
    if kind == 'agent':
        agent = Agent(
            name=obj_data['name'],
            description=obj_data.get('description'),
            instructions=obj_data.get('instructions'),
            default_model=obj_data.get('default_model'),
            temperature=obj_data.get('temperature'),
            max_output_tokens=obj_data.get('max_output_tokens')
        )
        session.add(agent)
        print(f"  ✓ Created Agent: {obj_data['name']}")
        
    elif kind == 'skill':
        skill = Skill(
            name=obj_data['name'],
            description=obj_data.get('description'),
            instructions=obj_data.get('instructions'),
            default_model=obj_data.get('default_model'),
            temperature=obj_data.get('temperature'),
            max_output_tokens=obj_data.get('max_output_tokens'),
            output_key=obj_data.get('output_key')
        )
        session.add(skill)
        print(f"  ✓ Created Skill: {obj_data['name']}")
        
    elif kind == 'tool':
        tool = Tool(
            name=obj_data['name'],
            description=obj_data.get('description'),
            tool_type=obj_data.get('tool_type', 'function'),
            config=obj_data.get('config', {})
        )
        session.add(tool)
        print(f"  ✓ Created Tool: {obj_data['name']}")
        
    elif kind == 'connector':
        connector = Connector(
            provider=obj_data['provider'],
            config=obj_data.get('config', {})
        )
        session.add(connector)
        print(f"  ✓ Created Connector: {obj_data['provider']}")
        
    elif kind == 'mcp' or kind == 'mcpconfig':
        mcp = MCPConfig(
            name=obj_data['name'],
            url=obj_data.get('url'),
            config=obj_data.get('config', {})
        )
        session.add(mcp)
        print(f"  ✓ Created MCP Config: {obj_data['name']}")
        
    else:
        print(f"  ⚠️  Unknown kind: {kind} for object: {obj_data.get('name', 'unnamed')}")


def initialize_database(db_url: str, data_dir: Path) -> None:
    """Initialize database with data from YAML files."""
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║               Database Initialization                         ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    # Set database URL in environment
    os.environ['WOWBITS_DB_CONNECTION_STRING'] = db_url
    
    # Create database tables
    create_database_tables(db_url)
    
    # Load YAML files
    print("\nLoading initialization data...\n")
    objects = load_yaml_files(data_dir)
    
    if not objects:
        print("\n⚠️  No objects to initialize")
        return
    
    print(f"\nFound {len(objects)} objects to initialize\n")
    
    # Create objects in database
    try:
        with get_session_context() as session:
            for obj_data in objects:
                try:
                    # create_object_from_yaml(session, obj_data)
                    print (f"skipping {obj_data.get('name', 'unnamed')}")
                except Exception as e:
                    print(f"  ❌ Error creating {obj_data.get('name', 'unnamed')}: {e}")
        
        print(f"\n✅ Database initialization complete!")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        raise


def save_db_config(db_url: str) -> None:
    """Save database configuration to .env file."""
    
    # Get root directory from environment variable
    root_dir = os.getenv('WOWBITS_ROOT_DIR')
    if not root_dir:
        raise ValueError("WOWBITS_ROOT_DIR environment variable is not set")
    env_file = Path(root_dir) / ".env"
    
    try:
        # Read existing .env if it exists
        existing_lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                existing_lines = [line for line in f.readlines() if not line.startswith('WOWBITS_DB_CONNECTION_STRING=')]
        
        # Write updated .env
        with open(env_file, 'w') as f:
            f.writelines(existing_lines)
            f.write(f"WOWBITS_DB_CONNECTION_STRING={db_url}\n")
        
        print(f"\n✅ Database configuration saved to: {env_file}")
        
    except Exception as e:
        print(f"\n⚠️  Could not save configuration to .env: {e}")


def run_setup(root_path: Optional[Path] = None) -> None:
    """Run the setup process.
    
    Args:
        root_path: Optional root directory path. If provided, SQLite database
                   will be automatically created in root_path/data/wowbits.db
    """
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║               WowBits Setup Wizard                            ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    try:
        # Get database connection string (passing root_path for SQLite auto-config)
        db_url = get_db_connection_string(root_path)
        
        # Save configuration
        save_db_config(db_url)
        
        # Get data directory - use root_path/data if available
        if root_path:
            data_dir = root_path / "data"
        else:
            src_dir = Path(__file__).parent.parent
            data_dir = src_dir.parent / "data"
        
        # Initialize database
        initialize_database(db_url, data_dir)
        
        # Scan and create Python functions from the functions directory
        if root_path:
            functions_dir = root_path / "functions"
            scan_and_create_functions(functions_dir)
        
        print("\n╔═══════════════════════════════════════════════════════════════╗")
        print("║               Setup Complete!                                 ║")
        print("╚═══════════════════════════════════════════════════════════════╝\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_setup()

