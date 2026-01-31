"""Interactive configuration wizard for mfcli."""
import os
import sys
from pathlib import Path
from typing import Optional

from mfcli.utils.directory_manager import app_dirs


def get_env_path() -> Path:
    """Get the path to the .env file."""
    return app_dirs.env_file_path


def read_existing_env() -> dict:
    """Read existing environment variables from .env file."""
    env_path = get_env_path()
    env_vars = {}
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars


def write_env_file(env_vars: dict) -> None:
    """Write environment variables to .env file."""
    env_path = get_env_path()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read the template
    template_path = Path(__file__).parent.parent / '.env.example'
    if not template_path.exists():
        # Fallback: create basic template
        template_content = []
        for key in env_vars:
            template_content.append(f"{key}={env_vars[key]}")
        content = '\n'.join(template_content)
    else:
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Replace placeholder values with actual values
        content = template_content
        for key, value in env_vars.items():
            # Replace the placeholder value in the template
            content = content.replace(f"{key}=your_{key.lower()}_here", f"{key}={value}")
            content = content.replace(f"{key}=your_{key.replace('_', ' ').lower()}_here", f"{key}={value}")
            # Handle specific patterns
            if key == 'google_api_key':
                content = content.replace(f"{key}=your_google_api_key_here", f"{key}={value}")
            elif key == 'openai_api_key':
                content = content.replace(f"{key}=your_openai_api_key_here", f"{key}={value}")
            elif key == 'digikey_client_id':
                content = content.replace(f"{key}=your_digikey_client_id_here", f"{key}={value}")
            elif key == 'digikey_client_secret':
                content = content.replace(f"{key}=your_digikey_client_secret_here", f"{key}={value}")
    
    with open(env_path, 'w') as f:
        f.write(content)


def prompt_for_value(
    key: str,
    description: str,
    link: Optional[str] = None,
    current_value: Optional[str] = None,
    required: bool = True
) -> Optional[str]:
    """Prompt user for a configuration value."""
    print(f"\n{'='*70}")
    print(f"  {description}")
    if link:
        print(f"  Get your key: {link}")
    if current_value and current_value != f"your_{key.lower()}_here":
        print(f"  Current value: {current_value[:20]}..." if len(current_value) > 20 else f"  Current value: {current_value}")
        prompt = f"  Enter new value (press Enter to keep current): "
    else:
        prompt = f"  Enter value{' (required)' if required else ' (optional)'}: "
    
    print(f"{'='*70}")
    
    value = input(prompt).strip()
    
    if not value:
        if current_value and current_value != f"your_{key.lower()}_here":
            return current_value
        elif not required:
            return None
        else:
            print("  ❌ This value is required!")
            return prompt_for_value(key, description, link, current_value, required)
    
    return value


def validate_api_key(key_name: str, api_key: str) -> bool:
    """Validate an API key by making a test request."""
    print(f"\n  Validating {key_name}...", end=' ')
    sys.stdout.flush()
    
    try:
        if key_name == "Google API":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            # Test with a simple list models call
            list(genai.list_models())
            print("✅")
            return True
        
        elif key_name == "OpenAI API":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            # Test with a simple models list call
            client.models.list()
            print("✅")
            return True
        
        
        elif key_name == "DigiKey API":
            # DigiKey validation would require OAuth flow, so we'll just check format
            if len(api_key) > 10:
                print("✅ (format check)")
                return True
            else:
                print("❌ Invalid format")
                return False
        
    except Exception as e:
        print(f"❌ ({str(e)[:50]}...)")
        return False
    
    return True


def run_configuration_wizard() -> None:
    """Run the interactive configuration wizard."""
    print("\n" + "="*70)
    print("  MFCLI CONFIGURATION WIZARD")
    print("="*70)
    print("\n  This wizard will help you configure mfcli with your API keys.")
    print("  You can press Ctrl+C at any time to exit.\n")
    
    try:
        # Read existing configuration
        existing_env = read_existing_env()
        new_env = existing_env.copy()
        
        # Google API Key
        value = prompt_for_value(
            "google_api_key",
            "Google Gemini API Key",
            "https://aistudio.google.com/app/apikey",
            existing_env.get("google_api_key"),
            required=True
        )
        if value:
            new_env["google_api_key"] = value
            validate_api_key("Google API", value)
        
        # OpenAI API Key
        value = prompt_for_value(
            "openai_api_key",
            "OpenAI API Key (for embeddings)",
            "https://platform.openai.com/api-keys",
            existing_env.get("openai_api_key"),
            required=True
        )
        if value:
            new_env["openai_api_key"] = value
            validate_api_key("OpenAI API", value)
        
        # DigiKey Client ID
        value = prompt_for_value(
            "digikey_client_id",
            "DigiKey Client ID (for datasheet downloads)",
            "https://developer.digikey.com/",
            existing_env.get("digikey_client_id"),
            required=True
        )
        if value:
            new_env["digikey_client_id"] = value
            validate_api_key("DigiKey API", value)
        
        # DigiKey Client Secret
        value = prompt_for_value(
            "digikey_client_secret",
            "DigiKey Client Secret",
            None,
            existing_env.get("digikey_client_secret"),
            required=True
        )
        if value:
            new_env["digikey_client_secret"] = value
        
        # Embedding configuration
        print("\n" + "="*70)
        print("  Vector Database Configuration")
        print("="*70)
        print("  Using default values:")
        print("  - Chunk size: 1000")
        print("  - Chunk overlap: 200")
        print("  - Embedding model: text-embedding-3-small")
        print("  - Embedding dimensions: 1536")
        
        change_defaults = input("\n  Change these defaults? (y/N): ").strip().lower()
        
        if change_defaults == 'y':
            value = input("  Chunk size [1000]: ").strip()
            new_env["chunk_size"] = value if value else "1000"
            
            value = input("  Chunk overlap [200]: ").strip()
            new_env["chunk_overlap"] = value if value else "200"
            
            value = input("  Embedding model [text-embedding-3-small]: ").strip()
            new_env["embedding_model"] = value if value else "text-embedding-3-small"
            
            value = input("  Embedding dimensions [1536]: ").strip()
            new_env["embedding_dimensions"] = value if value else "1536"
        else:
            new_env["chunk_size"] = existing_env.get("chunk_size", "1000")
            new_env["chunk_overlap"] = existing_env.get("chunk_overlap", "200")
            new_env["embedding_model"] = existing_env.get("embedding_model", "text-embedding-3-small")
            new_env["embedding_dimensions"] = existing_env.get("embedding_dimensions", "1536")
        
        # Write configuration
        write_env_file(new_env)
        
        env_path = get_env_path()
        print("\n" + "="*70)
        print("  ✅ Configuration saved successfully!")
        print(f"  Location: {env_path}")
        print("="*70)
        print("\n  Next steps:")
        print("  1. Run 'mfcli init' in your hardware project directory")
        print("  2. Run 'mfcli run' to process your documents")
        print("  3. (Optional) Run 'mfcli setup-mcp' to configure MCP server")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Configuration cancelled.")
        sys.exit(0)


def check_configuration() -> None:
    """Check and validate existing configuration."""
    print("\n" + "="*70)
    print("  CONFIGURATION CHECK")
    print("="*70)
    
    env_path = get_env_path()
    
    if not env_path.exists():
        print(f"\n  ❌ Configuration file not found: {env_path}")
        print("\n  Run 'mfcli configure' to create your configuration.")
        return
    
    print(f"\n  Configuration file: {env_path}")
    
    env_vars = read_existing_env()
    
    required_keys = [
        ("google_api_key", "Google Gemini API"),
        ("openai_api_key", "OpenAI API"),
        ("digikey_client_id", "DigiKey Client ID"),
        ("digikey_client_secret", "DigiKey Client Secret"),
    ]
    
    print("\n  Checking configuration:")
    all_valid = True
    
    for key, name in required_keys:
        value = env_vars.get(key)
        if not value or value.startswith("your_"):
            print(f"    ❌ {name}: Not configured")
            all_valid = False
        else:
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"    ✅ {name}: {masked_value}")
    
    print("\n  Vector database configuration:")
    print(f"    - Chunk size: {env_vars.get('chunk_size', 'Not set')}")
    print(f"    - Chunk overlap: {env_vars.get('chunk_overlap', 'Not set')}")
    print(f"    - Embedding model: {env_vars.get('embedding_model', 'Not set')}")
    print(f"    - Embedding dimensions: {env_vars.get('embedding_dimensions', 'Not set')}")
    
    if all_valid:
        print("\n  ✅ All required configuration values are set!")
        print("\n  To validate API keys, run: mfcli doctor")
    else:
        print("\n  ⚠️  Some configuration values are missing.")
        print("  Run 'mfcli configure' to complete your configuration.")
    
    print("="*70 + "\n")


def set_log_level(level: str = None) -> None:
    """View or set the logging level in the .env file."""
    env_path = get_env_path()
    
    # If no level provided, display current level
    if level is None:
        if not env_path.exists():
            print("\n" + "="*70)
            print("  CURRENT LOG LEVEL")
            print("="*70)
            print("\n  ⚠️  Configuration file not found.")
            print(f"  Expected location: {env_path}")
            print("\n  Using default: INFO")
            print("\n  Run 'mfcli log-level <LEVEL>' to set a log level.")
            print("  Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL")
            print("="*70 + "\n")
            return
        
        # Read current log level
        env_vars = read_existing_env()
        current_level = env_vars.get('log_level', env_vars.get('LOG_LEVEL', 'INFO'))
        
        print("\n" + "="*70)
        print("  CURRENT LOG LEVEL")
        print("="*70)
        print(f"\n  Current level: {current_level}")
        print(f"  Configuration file: {env_path}")
        print("\n  To change the log level, run:")
        print("  mfcli log-level <LEVEL>")
        print("\n  Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        print("="*70 + "\n")
        return
    
    # Ensure the env file exists
    if not env_path.exists():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.touch()
    
    # Read the existing file content
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Check if log_level already exists
    updated = False
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('log_level=') or stripped.startswith('LOG_LEVEL='):
            # Replace existing log_level
            new_lines.append(f"log_level={level}\n")
            updated = True
        else:
            new_lines.append(line)
    
    # If log_level wasn't found, add it
    if not updated:
        # Add it after configuration section or at the end
        new_lines.append(f"\n# Logging Configuration\n")
        new_lines.append(f"log_level={level}\n")
    
    # Write back to file
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print("\n" + "="*70)
    print("  LOG LEVEL UPDATED")
    print("="*70)
    print(f"\n  ✅ Log level set to: {level}")
    print(f"  Configuration file: {env_path}")
    print("\n  This will take effect on the next mfcli command.")
    print("="*70 + "\n")
