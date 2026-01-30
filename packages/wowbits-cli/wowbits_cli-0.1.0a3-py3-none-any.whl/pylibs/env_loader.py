import os
from pathlib import Path
from dotenv import load_dotenv


def load_env_variables():
    """
    Load environment variables from WOWBITS_ROOT_DIR/.env file.
    
    This function checks for the WOWBITS_ROOT_DIR environment variable
    and loads the .env file from that directory if it exists.
    """
    # WOWBITS_ROOT_DIR should be set in your shell profile (.bashrc or .zshrc)
    wowbits_root = os.getenv("WOWBITS_ROOT_DIR")
    if not wowbits_root:
        raise ValueError(
            "WOWBITS_ROOT_DIR environment variable not set.\n"
            "Please add it to your shell profile (.bashrc or .zshrc):\n"
            "export WOWBITS_ROOT_DIR=/path/to/wowbits"
        )
    print(f"WOWBITS_ROOT_DIR: {wowbits_root}")
    if wowbits_root:
        env_path = Path(wowbits_root) / ".env"
        print(f"Loading environment variables from {env_path}")
        if env_path.exists():
            load_dotenv(env_path)
        else:
            print(f"Warning: .env file not found at {env_path}")
    else:
        # Fallback to loading from current directory
        load_dotenv()
