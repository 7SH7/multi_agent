import json
from pathlib import Path

# Load issue database from JSON
issue_db_path = Path(__file__).parent / "issue_database.json"
if issue_db_path.exists():
    with open(issue_db_path, 'r', encoding='utf-8') as f:
        _issue_data = json.load(f)
    ISSUE_DATABASE = _issue_data.get("ISSUE_DATABASE", {})
    ISSUE_CATEGORIES = _issue_data.get("ISSUE_CATEGORIES", {})
    SEVERITY_LEVELS = _issue_data.get("SEVERITY_LEVELS", {})
else:
    ISSUE_DATABASE, ISSUE_CATEGORIES, SEVERITY_LEVELS = {}, {}, {}
