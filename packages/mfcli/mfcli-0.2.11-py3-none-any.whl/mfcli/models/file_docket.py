import json
from pathlib import Path
from typing import List, Dict, Optional

from pydantic import BaseModel, Field


class FileDocketEntry(BaseModel):
    name: str
    path: str
    vectorize: bool
    sub_type: str
    md5: str | None = Field(default=None)
    is_datasheet: bool = Field(default=False)


class FileDocketEntries(BaseModel):
    entries: List[FileDocketEntry] = Field(default_factory=list)

    def add(self, entry: FileDocketEntry):
        self.entries.append(entry)


class FileDocket:
    def __init__(self):
        self._docket = FileDocketEntries()
        self._md5_entry_map: Dict[str, FileDocketEntry] = {}
        self._path_entry_map: Dict[str, FileDocketEntry] = {}

    def add(self, entry: FileDocketEntry):
        self._docket.add(entry)
        if entry.md5:
            self._md5_entry_map[entry.md5] = entry
        # Use normalized path as key (convert to lowercase for case-insensitive comparison on Windows)
        normalized_path = Path(entry.path).as_posix().lower()
        self._path_entry_map[normalized_path] = entry

    def get_by_md5(self, md5: str) -> Optional[FileDocketEntry]:
        return self._md5_entry_map.get(md5)
    
    def get_by_path(self, path: str) -> Optional[FileDocketEntry]:
        normalized_path = Path(path).as_posix().lower()
        return self._path_entry_map.get(normalized_path)

    def remove(self, entry: FileDocketEntry):
        """Remove an entry from the docket"""
        if entry in self._docket.entries:
            self._docket.entries.remove(entry)
        if entry.md5 and entry.md5 in self._md5_entry_map:
            del self._md5_entry_map[entry.md5]
        normalized_path = Path(entry.path).as_posix().lower()
        if normalized_path in self._path_entry_map:
            del self._path_entry_map[normalized_path]

    def load_from_json(self, json_path: Path):
        """Load existing file docket from JSON file"""
        if not json_path.exists():
            return
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Convert the saved format back to entries
            all_entries = []
            for category in ['hw_files', 'datasheets', 'cheat_sheets']:
                if category in data:
                    all_entries.extend(data[category])
            
            # Create FileDocketEntry objects and add them
            for entry_data in all_entries:
                entry = FileDocketEntry(**entry_data)
                self.add(entry)
                
        except Exception as e:
            # If there's an error loading, just start fresh
            print(f"Warning: Could not load existing file_docket.json: {e}")

    def get_entries(self) -> Dict:
        datasheets = []
        cheat_sheets = []
        hw_files = []
        for entry in self._docket.entries:
            if entry.is_datasheet:
                datasheets.append(entry.model_dump())
            elif entry.sub_type == "CHEAT_SHEET":
                cheat_sheets.append(entry.model_dump())
            else:
                hw_files.append(entry.model_dump())
        return {
            "hw_files": hw_files,
            "datasheets": datasheets,
            "cheat_sheets": cheat_sheets
        }
