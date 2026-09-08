import os
import json
import threading
from typing import Dict, Any

class SettingsManager:
    """
    Thread-safe manager for persisting application settings to a local JSON file.
    Ensures that API keys and configurations survive app restarts.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SettingsManager, cls).__new__(cls)
                    cls._instance._init_once()
        return cls._instance

    def _init_once(self):
        # Store settings in APPDATA so they survive executable rebuilds
        app_data = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "ShohojMacro")
        os.makedirs(app_data, exist_ok=True)
        self.settings_file = os.path.join(app_data, "settings.json")
        self.settings_lock = threading.Lock()
        
        # Default Settings Configuration
        self.default_settings = {
            "ai": {
                "openrouter_api_key": "",
                "model": "google/gemini-flash-1.5",
                "humanizer_speed_multiplier": 1.0
            },
            "captcha": {
                "custom_prompt": "You are a CAPTCHA solver. The instruction is: '{instruction}'. This is a grid of images. The grid is numbered 1 to 9 from left to right, top to bottom. Which grid positions contain the target object? Return ONLY a JSON array of integers, for example: [1, 4, 7].",
                "max_retry_rounds": 4
            },
            "nst": {
                "api_key": "",
                "local_url": "http://localhost:8848",
                "enable_gui_fallback": True
            },
            "state": {
                "last_target_url": "",
                "last_macro_path": "",
                "last_csv_path": ""
            }
        }
        
        self.config: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.settings_file):
            return self.default_settings.copy()
            
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                
            # Merge loaded settings with defaults to ensure all keys exist
            merged = self.default_settings.copy()
            for category, values in loaded.items():
                if category in merged and isinstance(values, dict):
                    merged[category].update(values)
            return merged
        except Exception as e:
            print(f"[SettingsManager] Error loading settings: {e}")
            return self.default_settings.copy()

    def save(self) -> bool:
        """Flushes current config state to disk."""
        with self.settings_lock:
            try:
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4)
                return True
            except Exception as e:
                print(f"[SettingsManager] Error saving settings: {e}")
                return False

    def get(self, category: str, key: str, default: Any = None) -> Any:
        with self.settings_lock:
            cat_dict = self.config.get(category, {})
            return cat_dict.get(key, default)

    def set(self, category: str, key: str, value: Any):
        with self.settings_lock:
            if category not in self.config:
                self.config[category] = {}
            self.config[category][key] = value

    def update_category(self, category: str, new_values: Dict[str, Any]):
        """Updates multiple values within a single category and auto-saves."""
        with self.settings_lock:
            if category not in self.config:
                self.config[category] = {}
            self.config[category].update(new_values)
        self.save()
