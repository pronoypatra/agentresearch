"""
Notation Database

Stores unified notation and mappings.
"""

from typing import Dict, List, Optional
import json
from notation_resolution.unified_notation_builder import UnifiedNotationTable


class NotationDB:
    """
    Database for storing unified notation.
    """
    
    def __init__(self, db_path: str = "knowledge_base/notation.json"):
        """
        Initialize notation database.
        
        Args:
            db_path: Path to JSON file for storage
        """
        self.db_path = db_path
        self.unified_table: Optional[UnifiedNotationTable] = None
        self._load()
    
    def _load(self):
        """Load notation from disk"""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                # Reconstruct UnifiedNotationTable from dict
                # (simplified - in production would need proper deserialization)
                pass
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading notation database: {e}")
    
    def _save(self):
        """Save notation to disk"""
        try:
            if self.unified_table:
                data = self.unified_table.to_dict()
                with open(self.db_path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving notation database: {e}")
    
    def store_unified_table(self, table: UnifiedNotationTable):
        """Store unified notation table"""
        self.unified_table = table
        self._save()
    
    def get_unified_table(self) -> Optional[UnifiedNotationTable]:
        """Get unified notation table"""
        return self.unified_table

