"""
Persistent user progress — saves and loads completion data to/from progress.json
located in the project root directory.
"""

import json
import os

_PROGRESS_FILE = os.path.join(os.path.dirname(__file__), '..', 'progress.json')


def _path() -> str:
    return os.path.abspath(_PROGRESS_FILE)


def load_progress(user_data: dict) -> None:
    """Load saved progress into user_data in-place. Safe to call if file doesn't exist."""
    try:
        p = _path()
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            user_data['completed_scenarios'] = saved.get(
                'completed_scenarios', user_data['completed_scenarios']
            )
            user_data['learning_modules_completed'] = saved.get(
                'learning_modules_completed', user_data['learning_modules_completed']
            )
    except Exception as e:
        print(f"[progress] Could not load progress: {e}")


def save_progress(user_data: dict) -> None:
    """Persist the current user_data progress fields to disk."""
    try:
        data = {
            'completed_scenarios': user_data['completed_scenarios'],
            'learning_modules_completed': user_data['learning_modules_completed'],
        }
        with open(_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[progress] Could not save progress: {e}")


def mark_scenario_complete(user_data: dict, scenario_id: str) -> None:
    """Add scenario_id to completed list (if not already there) and persist."""
    if scenario_id not in user_data['completed_scenarios']:
        user_data['completed_scenarios'].append(scenario_id)
    save_progress(user_data)


def is_scenario_complete(user_data: dict, scenario_id: str) -> bool:
    """Return True if the given scenario has been completed."""
    return scenario_id in user_data['completed_scenarios']
