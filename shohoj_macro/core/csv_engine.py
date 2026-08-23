"""
Dynamic CSV Data Engine for Automated Form Filling & Registration
Parses CSV datasets with auto-encoding detection (UTF-8, BOM, Latin-1) and handles {{variable}} templating.
"""

import csv
import re
from typing import Optional


class CSVDataEngine:
    """Manages CSV dataset loading, row iteration, and variable interpolation."""

    def __init__(self):
        self.filepath: Optional[str] = None
        self.headers: list[str] = []
        self.rows: list[dict[str, str]] = []
        self.current_row_idx: int = 0
        self.is_loaded: bool = False

    def load_file(self, path: str) -> tuple[bool, str]:
        """
        Loads and parses a CSV file with automatic encoding fallback.
        Returns (success: bool, message: str).
        """
        encodings_to_try = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
        content = None
        used_encoding = ""

        for enc in encodings_to_try:
            try:
                with open(path, "r", encoding=enc) as f:
                    content = f.read()
                    used_encoding = enc
                    break
            except Exception:
                continue

        if content is None:
            return False, f"Failed to read file '{path}' with supported encodings."

        try:
            # Parse CSV content
            lines = content.splitlines()
            reader = csv.reader(lines)
            raw_rows = list(reader)

            if not raw_rows:
                return False, "CSV file is completely empty."

            # Normalize headers (strip whitespace)
            self.headers = [h.strip() for h in raw_rows[0] if h.strip()]
            if not self.headers:
                return False, "No valid column headers found in first row."

            self.rows.clear()
            for r_idx, row in enumerate(raw_rows[1:], start=1):
                if not any(row):  # Skip completely empty rows
                    continue
                row_dict = {}
                for col_idx, col_name in enumerate(self.headers):
                    val = row[col_idx].strip() if col_idx < len(row) else ""
                    row_dict[col_name] = val
                self.rows.append(row_dict)

            self.filepath = path
            self.current_row_idx = 0
            self.is_loaded = True
            return True, f"Loaded {len(self.rows)} rows ({len(self.headers)} columns) using {used_encoding}."

        except Exception as e:
            return False, f"CSV parsing error: {e}"

    def clear(self):
        self.filepath = None
        self.headers.clear()
        self.rows.clear()
        self.current_row_idx = 0
        self.is_loaded = False

    def get_row_count(self) -> int:
        return len(self.rows)

    def get_row_data(self, row_idx: int) -> dict[str, str]:
        if not self.rows or row_idx < 0 or row_idx >= len(self.rows):
            return {}
        return dict(self.rows[row_idx])

    def interpolate_text(self, template_text: str, row_idx: int) -> str:
        """
        Replaces {{variable}} patterns with row values.
        E.g. "Hello {{first_name}}" -> "Hello John".
        """
        if not template_text or not self.rows:
            return template_text

        row_data = self.get_row_data(row_idx)
        if not row_data:
            return template_text

        def _replacer(match):
            var_name = match.group(1).strip()
            return row_data.get(var_name, match.group(0))

        return re.sub(r"\{\{([^}]+)\}\}", _replacer, template_text)

    def extract_variables(self, text: str) -> list[str]:
        """Extracts all {{variable}} names found in text."""
        return [m.strip() for m in re.findall(r"\{\{([^}]+)\}\}", text)]

    def validate_variables(self, text: str) -> list[str]:
        """Returns any variable names present in text that do NOT exist in CSV headers."""
        if not self.is_loaded:
            return self.extract_variables(text)
        vars_in_text = self.extract_variables(text)
        return [v for v in vars_in_text if v not in self.headers]
