import os
from pathlib import Path

def load_env():
    """
    Loads environment variables from a .env file in the current working directory
    or the project root. Does not override existing environment variables.
    """
    # Look for .env in current directory
    env_path = Path(".env")
    if not env_path.exists():
        # Fallback: traverse up to find .env (simple check for parent/root)
        # Assuming we might be running from inside a package subdir
        parent_env = Path("..") / ".env"
        if parent_env.exists():
            env_path = parent_env
        else:
             # Try one more level up for typical project structure
            root_env = Path("../..") / ".env"
            if root_env.exists():
                env_path = root_env
            else:
                return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]

                    if key and key not in os.environ:
                        os.environ[key] = value
    except Exception:
        # Silently fail if .env is unreadable, as this is optional config
        pass

def load_config() -> dict:
    """
    Loads configuration from ~/.config/clippy/config.yml.
    Creates default config if missing.
    Returns a dict with config values.
    """
    config_dir = Path.home() / ".config" / "clippy"
    config_file = config_dir / "config.yml"
    
    default_config = {
        "ai": {
            "enabled": False,
            "backend": "azure",
            "confidence_threshold": 0.6
        },
        "knowledge": {
            "use_man_pages": True,
            "user_knowledge_dir": str(config_dir / "knowledge")
        }
    }
    
    # Create default config if missing
    if not config_file.exists():
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                f.write("# Clippy Configuration\n")
                f.write("ai:\n")
                f.write("  enabled: false\n")
                f.write("  backend: azure\n")
                f.write("  confidence_threshold: 0.6\n")
                f.write("knowledge:\n")
                f.write("  use_man_pages: true\n")
                f.write(f"  user_knowledge_dir: {default_config['knowledge']['user_knowledge_dir']}\n")
        except Exception:
            return default_config

    # Parse config (Manual parser to avoid PyYAML dependency)
    # Supports simple 2-level nested keys
    config = default_config.copy()
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        current_section = None
        for line in lines:
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue
            
            stripped = line.strip()
            
            # Detect section headers (e.g. "ai:")
            if line.endswith(":") and not line.startswith(" "):
                current_section = line[:-1]
                if current_section not in config:
                    config[current_section] = {}
                continue

            # Detect key-values (e.g. "  enabled: true")
            if current_section and ":" in stripped:
                key, val = stripped.split(":", 1)
                key = key.strip()
                val = val.strip().lower()
                
                # Parse types
                if val == "true":
                    parsed_val = True
                elif val == "false":
                    parsed_val = False
                else:
                    try:
                        parsed_val = float(val) if "." in val else int(val)
                    except ValueError:
                        parsed_val = val # String fallback
                
                config[current_section][key] = parsed_val
                
    except Exception:
        return default_config
        
    return config
