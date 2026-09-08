"""
Dynamic CSV Data Engine for Automated Form Filling & Registration
Parses CSV datasets with auto-encoding detection (UTF-8, BOM, Latin-1) and handles {{variable}} templating.
"""

import os
import csv
import re
from typing import Optional, Callable


class CSVDataEngine:
    """Manages CSV dataset loading, row iteration, and variable interpolation."""

    def __init__(self):
        self.filepath: Optional[str] = None
        self.headers: list[str] = []
        self.rows: list[dict[str, str]] = []
        self.current_row_idx: int = 0
        self.is_loaded: bool = False
        self.on_status_change: Optional[Callable[[int, str], None]] = None

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

    def get_headers(self) -> list[str]:
        return list(self.headers)

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

        import datetime
        try:
            from dateutil import parser as date_parser
        except ImportError:
            date_parser = None

        def _replacer(match):
            full_var = match.group(1).strip()
            
            # Check for formatting pipeline (e.g. {{Birthday|MM/DD/YYYY}})
            if "|" in full_var:
                var_name, fmt = full_var.split("|", 1)
                var_name = var_name.strip()
                fmt = fmt.strip()
                
                raw_val = row_data.get(var_name, "")
                if not raw_val:
                    return raw_val
                    
                try:
                    if date_parser:
                        parsed_date = date_parser.parse(raw_val)
                    else:
                        parsed_date = datetime.datetime.strptime(raw_val, "%Y-%m-%d")
                    
                    # Convert python strftime format (MM/DD/YYYY -> %m/%d/%Y)
                    py_fmt = fmt.replace("MM", "%m").replace("DD", "%d").replace("YYYY", "%Y").replace("YY", "%y")
                    return parsed_date.strftime(py_fmt)
                except Exception:
                    # If parsing fails, just return the raw value
                    return raw_val
            else:
                var_name = full_var

            return row_data.get(var_name, match.group(0))

        return re.sub(r"\{\{([^}]+)\}\}", _replacer, template_text)

    def mark_row_status(self, row_idx: int, status_col: str, status: str):
        """
        Logs the status in memory, updates CSV file on disk, and triggers UI update.
        Fills existing 'Status' column, or the last blank cell of the row, or appends a 'Status' column.
        """
        if 0 <= row_idx < len(self.rows):
            self.rows[row_idx]['_macro_status'] = status
            
            status_header = None
            if status_col and status_col in self.headers:
                status_header = status_col
            elif "Status" in self.headers:
                status_header = "Status"
            else:
                # Check if the last column of this row is empty; if so, write into that blank cell
                if self.headers and self.rows[row_idx].get(self.headers[-1], "") == "":
                    status_header = self.headers[-1]
                else:
                    status_header = "Status"
                    self.headers.append(status_header)
            
            self.rows[row_idx][status_header] = status
            
            # Save back to CSV file if filepath exists
            if self.filepath and os.path.exists(self.filepath):
                try:
                    with open(self.filepath, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f)
                        writer.writerow(self.headers)
                        for r in self.rows:
                            row_vals = [r.get(h, "") for h in self.headers]
                            writer.writerow(row_vals)
                except Exception as e:
                    print(f"[CSVDataEngine] Failed to save updated status to disk: {e}")

            if self.on_status_change:
                self.on_status_change(row_idx, status)

    def extract_variables(self, text: str) -> list[str]:
        """Extracts all {{variable}} names found in text."""
        return [m.strip() for m in re.findall(r"\{\{([^}]+)\}\}", text)]

    def validate_variables(self, text: str) -> list[str]:
        """Returns any variable names present in text that do NOT exist in CSV headers."""
        if not self.is_loaded:
            return self.extract_variables(text)
        vars_in_text = self.extract_variables(text)
        return [v for v in vars_in_text if v not in self.headers]
