import json
from typing import Any
default_settings: dict[str, Any] = None
local_settings: dict[str, Any] = None
try:
    with open("default_settings.json", "r", encoding="utf-8") as f:
        default_settings = json.load(f)
except FileNotFoundError:
    print("Settings file not found")
except json.JSONDecodeError:
    print("Error decoding JSON")
try:
    with open("local_settings.json", "r", encoding="utf-8") as f:
        local_settings = json.load(f)
except FileNotFoundError:
    pass
except json.JSONDecodeError:
    print("Error decoding JSON")

print(default_settings , "\n", local_settings)