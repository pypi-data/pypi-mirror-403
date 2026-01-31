"""State manager for MCP server to persist state between calls."""
import json
from pathlib import Path
from typing import Optional

from mfcli.utils.directory_manager import app_dirs


class MCPStateManager:
    """Manages persistent state for the MCP server."""
    
    def __init__(self):
        state_dir = Path(app_dirs.app_data_dir)
        try:
            state_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If we can't create the directory, we'll operate with in-memory state only.
            pass
        self.state_file = state_dir / "mcp_state.json"
        self._state = self._load_state()
    
    def _load_state(self) -> dict:
        """Load state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_state(self):
        """Save state to disk."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self._state, f, indent=2)
        except Exception:
            pass  # Silently fail if we can't save state
    
    def get_last_project_name(self) -> Optional[str]:
        """Get the last used project name."""
        return self._state.get('last_project_name')
    
    def set_last_project_name(self, project_name: str):
        """Set the last used project name."""
        self._state['last_project_name'] = project_name
        self._save_state()


# Singleton instance
state_manager = MCPStateManager()
