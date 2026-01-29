#!/usr/bin/env python3
"""
WowBits CLI - Functions Command

Handles Python function management including listing, creating, and syncing functions.
"""

import sys
import os
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylibs.database_manager import get_session_context
from db.schema import PythonFunction


def list_functions() -> None:
    """List all Python functions in the database."""
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║               Python Functions                                ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    try:
        with get_session_context() as session:
            functions = session.query(PythonFunction).all()
            
            if not functions:
                print("  ℹ️  No functions found in database")
                return
            
            print(f"Found {len(functions)} function(s):\n")
            print(f"{'Name':<35} {'Description':<40}")
            print("-" * 75)
            
            for func in functions:
                name = func.name[:33] + ".." if len(func.name) > 35 else func.name
                desc = (func.description or "")[:38] + ".." if len(func.description or "") > 40 else (func.description or "-")
                print(f"{name:<35} {desc:<40}")
            
            print()
            
    except Exception as e:
        print(f"\n❌ Error listing functions: {e}")
        raise


def scan_and_create_functions(functions_dir: Path, verbose: bool = True) -> None:
    """
    Scan the functions directory and create/update PythonFunction entries in the database.
    
    Args:
        functions_dir: Path to the functions directory to scan
        verbose: Whether to print detailed output
    """
    if verbose:
        print("\n╔═══════════════════════════════════════════════════════════════╗")
        print("║               Python Functions Setup                          ║")
        print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    if not functions_dir.exists():
        print(f"⚠️  Functions directory not found: {functions_dir}")
        print("   Skipping function registration.")
        return
    
    # Install dependencies from functions/requirements.txt
    requirements_file = functions_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"📦 Installing dependencies from {requirements_file}...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("  ✓ Dependencies installed successfully\n")
            else:
                print(f"  ⚠️  Warning: Some dependencies may not have installed correctly")
                if result.stderr:
                    print(f"     {result.stderr}\n")
        except Exception as e:
            print(f"  ⚠️  Warning: Could not install dependencies: {e}\n")
    else:
        if verbose:
            print(f"ℹ️  No requirements.txt found in {functions_dir}\n")
    
    # Get all Python files in the functions directory
    python_files = [f for f in functions_dir.glob("*.py") 
                   if f.name not in ("__init__.py", "create_functions_in_db.py")]
    
    if not python_files:
        print(f"ℹ️  No Python function files found in: {functions_dir}")
        return
    
    print(f"Found {len(python_files)} Python function file(s) in {functions_dir}\n")
    
    try:
        with get_session_context() as session:
            created_count = 0
            updated_count = 0
            
            for py_file in python_files:
                function_name = py_file.stem  # Filename without .py extension
                
                try:
                    # Read the file content
                    with open(py_file, 'r') as f:
                        file_content = f.read()
                    
                    # Check if function already exists
                    existing_function = session.query(PythonFunction).filter(
                        PythonFunction.name == function_name
                    ).first()
                    
                    if existing_function:
                        if verbose:
                            print(f"  ℹ️  Function '{function_name}' already exists in database")
                        # Update existing function
                        existing_function.code = file_content
                        session.merge(existing_function)
                        print(f"  ↻ Updated: {function_name}")
                        updated_count += 1
                    else:
                        # Create new function entry
                        python_function = PythonFunction(
                            name=function_name,
                            description=function_name,  # Use filename as description
                            code=file_content
                        )
                        session.add(python_function)
                        print(f"  ✓ Created: {function_name}")
                        created_count += 1
                        
                except Exception as e:
                    print(f"  ❌ Error processing {function_name}: {e}")
            
            print(f"\n✅ Functions setup complete!")
            print(f"   Created: {created_count}, Updated: {updated_count}")
            
    except Exception as e:
        print(f"\n❌ Functions setup failed: {e}")
        raise


def get_functions_dir() -> Optional[Path]:
    """
    Get the functions directory from WOWBITS_ROOT_DIR environment variable.
    
    Returns:
        Path to the functions directory or None if not set
    """
    root_dir = os.environ.get("WOWBITS_ROOT_DIR")
    
    if not root_dir:
        # Try to load from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            root_dir = os.environ.get("WOWBITS_ROOT_DIR")
        except ImportError:
            pass
    
    if not root_dir:
        print("❌ Error: WOWBITS_ROOT_DIR environment variable is not set.")
        print("   Please run 'wowbits setup' first or set the environment variable.")
        return None
    
    return Path(root_dir) / "functions"


def handle_function_command(action: str) -> None:
    """
    Handle function CLI commands.
    
    Args:
        action: The action to perform (list, create)
    """
    if action == "list":
        list_functions()
    elif action == "create":
        functions_dir = get_functions_dir()
        if functions_dir:
            scan_and_create_functions(functions_dir)
    else:
        print(f"❌ Unknown function action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    # For testing purposes
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Python functions")
    parser.add_argument("action", choices=["list", "create"], help="Action to perform")
    
    args = parser.parse_args()
    handle_function_command(args.action)

