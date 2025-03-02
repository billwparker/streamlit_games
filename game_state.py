import os
import json
import time
import math
from dataclasses import asdict, is_dataclass
from typing import Dict, Any

# Custom JSON encoder to handle dataclasses and special values
class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)

# File to store game state between Streamlit reruns
STATE_FILE = os.path.join(os.path.dirname(__file__), "game_state.json")

def save_game_state(state: Dict[str, Any]) -> None:
    """Save game state to file to persist between Streamlit reruns"""
    try:
        with open(STATE_FILE, 'w') as f:
            # Convert dataclasses to dictionaries for JSON serialization
            serializable_state = {}
            for key, value in state.items():
                if key == 'last_update_time':
                    serializable_state[key] = value
                elif key in ['ship', 'asteroids', 'bullets']:
                    if key == 'ship' and value is not None:
                        serializable_state[key] = asdict(value)
                    elif key in ['asteroids', 'bullets']:
                        serializable_state[key] = [asdict(item) for item in value]
                else:
                    serializable_state[key] = value
                    
            json.dump(serializable_state, f, cls=DataclassJSONEncoder)
    except Exception as e:
        print(f"Error saving game state: {e}")

def load_game_state() -> Dict[str, Any]:
    """Load game state from file"""
    if not os.path.exists(STATE_FILE):
        return {}
    
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading game state: {e}")
        # If the file is corrupted or doesn't exist, return empty state
        return {}

def clear_game_state() -> None:
    """Remove the game state file"""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
