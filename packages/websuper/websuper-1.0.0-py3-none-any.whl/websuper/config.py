import json
from pathlib import Path

CONF = Path.home() / ".websuper.json"

def save_token(token):
    CONF.write_text(json.dumps({"token": token}))

def load_token():
    if not CONF.exists():
        print("No auth token found. Run: websuper config add-authtoken <TOKEN>")
        exit(1)
    return json.loads(CONF.read_text())["token"]
