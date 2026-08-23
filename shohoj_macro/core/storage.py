"""
Macro File Storage, JSON Serialization & Macro Library Indexer
Saves and loads native .shj (Shohoj Macro) files with author metadata and schema versioning.
"""

import json
import os
import time
from datetime import datetime
from shohoj_macro.version import (
    __app_name__,
    __version__,
    __author__,
    __username__,
    __file_format_version__,
)
from shohoj_macro.core.events import MacroEvent


class MacroStorage:
    """Handles .shj file persistence and library management."""

    @staticmethod
    def get_default_library_dir() -> str:
        """Returns standard user document path for Shohoj Macro."""
        user_docs = os.path.expanduser("~/Documents")
        path = os.path.join(user_docs, "Shohoj Macro")
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def save_macro_to_file(
        cls,
        filepath: str,
        events: list[MacroEvent],
        name: str = "Untitled Macro",
        description: str = "",
        tags: list[str] = None,
        default_loops: int = 1,
        default_speed: float = 1.0,
    ) -> bool:
        """Serializes macro event list to .shj JSON file."""
        if not filepath.endswith(".shj"):
            filepath += ".shj"

        payload = {
            "metadata": {
                "app": __app_name__,
                "app_version": __version__,
                "author": f"{__author__} ({__username__})",
                "format_version": __file_format_version__,
                "name": name,
                "description": description,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "event_count": len(events),
                "default_loops": default_loops,
                "default_speed": default_speed,
            },
            "events": [e.to_dict() for e in events],
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            return True
        except Exception as err:
            print(f"Error saving macro: {err}")
            return False

    @classmethod
    def load_macro_from_file(cls, filepath: str) -> tuple[list[MacroEvent], dict]:
        """Loads .shj file and returns (event_list, metadata_dict)."""
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Macro file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        raw_events = data.get("events", [])
        events = [MacroEvent.from_dict(item) for item in raw_events]
        return events, metadata

    @classmethod
    def list_library_macros(cls) -> list[dict]:
        """Scans the default library directory for available .shj macro files."""
        lib_dir = cls.get_default_library_dir()
        results = []

        if not os.path.exists(lib_dir):
            return results

        for root, _, files in os.walk(lib_dir):
            for file in files:
                if file.endswith(".shj"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        meta = data.get("metadata", {})
                        results.append({
                            "path": full_path,
                            "filename": file,
                            "name": meta.get("name", file[:-4]),
                            "description": meta.get("description", ""),
                            "event_count": meta.get("event_count", len(data.get("events", []))),
                            "tags": meta.get("tags", []),
                            "updated_at": meta.get("updated_at", ""),
                        })
                    except Exception:
                        results.append({
                            "path": full_path,
                            "filename": file,
                            "name": file[:-4],
                            "description": "Corrupted or invalid file",
                            "event_count": 0,
                            "tags": [],
                            "updated_at": "",
                        })

        return sorted(results, key=lambda x: x["name"])
