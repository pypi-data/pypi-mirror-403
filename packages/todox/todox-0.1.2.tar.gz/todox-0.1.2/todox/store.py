
import json
from pathlib import Path
from datetime import datetime

import os

DB_PATH = Path(os.environ.get("TODOX_DB_PATH", Path.home() / ".todox.json"))

def load():
    if not DB_PATH.exists():
        return {"todos": [], "last_active": None}
    return json.loads(DB_PATH.read_text())

def save(data):
    DB_PATH.write_text(json.dumps(data, indent=2))

def now():
    return datetime.now().isoformat()
