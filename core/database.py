from pymongo import MongoClient
from datetime import datetime, timezone
import hashlib
import uuid


connection_string = "mongodb+srv://joelheickert_db_user:uOYNtA7S9f2pJtxP@databasecyberlabs.zjrkets.mongodb.net/"

client = MongoClient(connection_string)

# choose database
db = client["databasecyberlabs"]

# choose collection
users_data = db["users"]
lessons_data = db["lessons"]
lessonsCompleted_data = db["lessonsComplete"]


def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def addUser(username, password, email, skill_level,
            profile_photo=None, description=None):
    """Add a new user. Returns (True, user_id) or (False, error_message)."""

    if users_data.find_one({"username": username}):
        return False, f"Username '{username}' is already taken."

    if users_data.find_one({"email": email}):
        return False, f"An account with that email already exists."

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    user = {
        "user_id":         user_id,
        "username":        username,
        "password_hashed": _hash_pw(password),
        "email":           email,
        "creation_date":   now,
        "last_login":      now,
        "profile_photo":   profile_photo,
        "description":     description,
        "skill_level":     skill_level,
    }

    users_data.insert_one(user)
    return True, user_id


def deleteUser(user_id):
    """Delete a user by user_id."""
    users_data.delete_one({"user_id": user_id})


def updateUser(user_id, **kwargs):
    """Update fields on a user document. Pass password= to re-hash automatically."""
    update_fields = {}
    for key, value in kwargs.items():
        if key == "password":
            update_fields["password_hashed"] = _hash_pw(value)
        else:
            update_fields[key] = value

    users_data.update_one({"user_id": user_id}, {"$set": update_fields})


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def checkUserExists(username: str) -> bool:
    """Return True if a username is already registered."""
    return users_data.find_one({"username": username}) is not None


def loginUser(username: str, password: str):
    """
    Attempt login.
    Returns (True, user_doc) on success or (False, error_message) on failure.
    """
    user = users_data.find_one({"username": username})
    if not user:
        return False, "Username not found."

    if user["password_hashed"] != _hash_pw(password):
        return False, "Incorrect password."

    # Update last_login timestamp
    users_data.update_one(
        {"username": username},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )

    return True, user


def resetPassword(username: str, email: str, new_password: str):
    """
    Reset a user's password after verifying their email matches.
    Returns (True, '') or (False, error_message).
    """
    user = users_data.find_one({"username": username})
    if not user:
        return False, "Username not found."

    if user.get("email", "").lower() != email.lower():
        return False, "Email does not match our records."

    users_data.update_one(
        {"username": username},
        {"$set": {"password_hashed": _hash_pw(new_password)}}
    )
    return True, ""


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

def getUserProgress(user_id):
    """Return list of completed lesson documents for a user."""
    return list(lessonsCompleted_data.find({"user_id": user_id}))


def completeLesson(user_id, lesson_id):
    """Mark a lesson as completed for a user."""
    lessonsCompleted_data.insert_one({
        "userID":                user_id,
        "lessonID":              lesson_id,
        "lesson_completion_date": datetime.now(timezone.utc),
        "is_completed":          True,
    })


# ---------------------------------------------------------------------------
# Profile helpers (added for profile view)
# ---------------------------------------------------------------------------

def getUser(user_id: str) -> dict:
    """
    Return a user document by user_id as a plain dict,
    with MongoDB's _id removed.
    Returns {} if not found.
    """
    user = users_data.find_one({"user_id": user_id}, {"_id": 0})
    return user or {}


def updateProfile(user_id: str, **kwargs):
    """
    Update profile-specific fields for a user.
    Accepted keys: description, skill_level, profile_photo.
    Uses updateUser internally so all update logic stays in one place.
    """
    allowed = {"description", "skill_level", "profile_photo"}
    filtered = {k: v for k, v in kwargs.items() if k in allowed}
    if filtered:
        updateUser(user_id, **filtered)


def markScenarioComplete(user_id: str, scenario_id: str):
    """
    Add scenario_id to the user's completed_scenarios list (no duplicates).
    Also calls completeLesson so progress is tracked in lessonsComplete too.
    """
    users_data.update_one(
        {"user_id": user_id},
        {"$addToSet": {"completed_scenarios": scenario_id}}
    )
    completeLesson(user_id, scenario_id)


def getCompletedScenarios(user_id: str) -> list:
    """Return the list of completed scenario IDs for a user."""
    user = users_data.find_one({"user_id": user_id}, {"completed_scenarios": 1, "_id": 0})
    if not user:
        return []
    return user.get("completed_scenarios", [])


# ---------------------------------------------------------------------------
# Quiz results
# ---------------------------------------------------------------------------

quiz_results_data = db["quizResults"]


def saveQuizResult(user_id: str, module_id: str, correct: bool, question: str = None):
    """Save a quiz answer result for a user."""
    quiz_results_data.insert_one({
        "user_id":     user_id,
        "module_id":   module_id,
        "question":    question,
        "correct":     correct,
        "answered_at": datetime.now(timezone.utc),
    })