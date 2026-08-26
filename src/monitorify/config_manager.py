import json
from pathlib import Path


class configManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_data = {}
        self.load_config()

    def load_config(self) -> dict:
        path = Path(self.config_path)
        if not path.exists():
            self.config_data = {}
            return self.config_data

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                self.config_data = data
            else:
                self.config_data = {}
        except (json.JSONDecodeError, OSError):
            self.config_data = {}

        return self.config_data

    def save_config(self, config_data: dict):
        try:
            path = Path(self.config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as file:
                json.dump(config_data, file, indent=4)
            self.config_data = config_data
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def get(self, key: str, default=None):
        return self.config_data.get(key, default)

    def get_connfig(self, key: str):
        return self.get(key, None)

    def set(self, key: str, value):
        self.config_data[key] = value
        self.save_config(self.config_data)
