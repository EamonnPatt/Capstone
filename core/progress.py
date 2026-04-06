"""
Persistent user progress — backed by MongoDB (via core.database).
A local progress.json fallback is kept for offline/dev use.
"""

import json
import os

_PROGRESS_FILE = os.path.join(os.path.dirname(__file__), '..', 'progress.json')


def _path() -> str:
    return os.path.abspath(_PROGRESS_FILE)


def load_progress(user_data: dict) -> None:
    """Ensure completed_scenarios key exists, then try loading from local JSON."""
    user_data.setdefault('completed_scenarios', [])
    user_data.setdefault('learning_modules_completed', [])
    try:
        p = _path()
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            for scenario_id in saved.get('completed_scenarios', []):
                if scenario_id not in user_data['completed_scenarios']:
                    user_data['completed_scenarios'].append(scenario_id)
            for module_id in saved.get('learning_modules_completed', []):
                if module_id not in user_data['learning_modules_completed']:
                    user_data['learning_modules_completed'].append(module_id)
    except Exception as e:
        print(f"[progress] Could not load progress: {e}")


def save_progress(user_data: dict) -> None:
    """Persist progress fields to disk."""
    try:
        data = {
            'completed_scenarios':       user_data.get('completed_scenarios', []),
            'learning_modules_completed': user_data.get('learning_modules_completed', []),
        }
        with open(_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[progress] Could not save progress: {e}")


def mark_scenario_complete(user_data: dict, scenario_id: str) -> None:
    """Add scenario_id to completed list, persist to MongoDB and local JSON."""
    completed = user_data.setdefault('completed_scenarios', [])
    if scenario_id not in completed:
        completed.append(scenario_id)

    # Persist to MongoDB if user_id is available
    if user_data.get('user_id'):
        try:
            import core.database as db
            db.markScenarioComplete(user_data['user_id'], scenario_id)
        except Exception as e:
            print(f"[progress] MongoDB write failed: {e}")

    save_progress(user_data)


def is_scenario_complete(user_data: dict, scenario_id: str) -> bool:
    """Return True if the given scenario has been completed."""
    return scenario_id in user_data.get('completed_scenarios', [])


def mark_module_complete(user_data: dict, module_id: str) -> None:
    """Add module_id to completed list, persist to MongoDB and local JSON."""
    completed = user_data.setdefault('learning_modules_completed', [])
    if module_id not in completed:
        completed.append(module_id)

    if user_data.get('user_id'):
        try:
            import core.database as db
            db.completeLesson(user_data['user_id'], module_id)
        except Exception as e:
            print(f"[progress] MongoDB write failed: {e}")

    save_progress(user_data)


def is_module_complete(user_data: dict, module_id: str) -> bool:
    """Return True if the given learning module has been completed."""
    return module_id in user_data.get('learning_modules_completed', [])
