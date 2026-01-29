"""
Storage backends for recordings (JSON and SQLite).

This module provides storage backends for caching AI API responses.
Supports both JSON file storage and SQLite database backends.
"""

import hashlib
import json
import logging
import os
import sqlite3
import time
from typing import Any, Optional, Dict, List

logger = logging.getLogger(__name__)


class Storage:
    """Handles saving and loading recordings."""
    
    def __init__(self, save_dir: str, backend: str = "sqlite"):
        """
        Initialize storage.
        
        Args:
            save_dir: Directory for storage files
            backend: "json" or "sqlite"
        """
        self.save_dir = save_dir
        self.backend = backend
        
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        if backend == "sqlite":
            self.db_path = os.path.join(save_dir, "recordings.db")
            self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                session_id TEXT,
                call_hash TEXT,
                data TEXT,
                timestamp REAL,
                cost REAL DEFAULT 0,
                PRIMARY KEY (session_id, call_hash)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session 
            ON recordings(session_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON recordings(timestamp)
        """)
        conn.commit()
        conn.close()
    
    def create_hash(self, args: tuple, kwargs: dict, version: str) -> str:
        """
        Create deterministic hash for function inputs.
        
        Args:
            args: Positional arguments
            kwargs: Keyword arguments
            version: Version string
        
        Returns:
            16-character hash
        """
        data = {
            "args": [self._serialize(arg) for arg in args],
            "kwargs": {k: self._serialize(v) for k, v in sorted(kwargs.items())},
            "version": version
        }
        
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _serialize(self, obj: Any) -> Any:
        """
        Convert object to JSON-serializable format.
        
        Handles custom objects by converting them to dictionaries,
        and properly serializes lists, sets, and nested structures.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable representation of the object
        """
        if hasattr(obj, '__dict__'):
            return {"__type__": type(obj).__name__, "__data__": self._serialize(obj.__dict__)}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize(item) for item in obj]
        elif isinstance(obj, set):
            return sorted([self._serialize(item) for item in obj], key=str)
        elif isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        return obj
    
    def save(self, session_id: str, call_hash: str, data: Dict[str, Any], cost: float = 0) -> None:
        """
        Save a recording to storage.
        
        Args:
            session_id: Unique session identifier
            call_hash: Hash of the function call
            data: Dictionary containing recording data
            cost: API call cost (default: 0)
        """
        if self.backend == "sqlite":
            self._save_sqlite(session_id, call_hash, data, cost)
        else:
            self._save_json(session_id, call_hash, data)
    
    def _save_sqlite(self, session_id: str, call_hash: str, data: Dict[str, Any], cost: float) -> None:
        """
        Save to SQLite database.
        
        Args:
            session_id: Session identifier
            call_hash: Call hash
            data: Recording data
            cost: API call cost
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO recordings VALUES (?, ?, ?, ?, ?)",
            (session_id, call_hash, json.dumps(data, default=str), time.time(), cost)
        )
        conn.commit()
        conn.close()
    
    def _save_json(self, session_id: str, call_hash: str, data: Dict[str, Any]) -> None:
        """
        Save to JSON file.
        
        Args:
            session_id: Session identifier
            call_hash: Call hash
            data: Recording data
        """
        file_path = os.path.join(self.save_dir, f"{session_id}.json")
        
        # Load existing data
        recordings = {}
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                recordings = json.load(f)
        
        # Add new recording
        recordings[call_hash] = data
        
        # Save back
        with open(file_path, 'w') as f:
            json.dump(recordings, f, indent=2, default=str)
    
    def load(self, session_id: str, call_hash: str, ttl: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Load a recording from storage.
        
        Args:
            session_id: Session identifier
            call_hash: Call hash
            ttl: Time-to-live in seconds (None = no expiration)
            
        Returns:
            Recording data if found and not expired, None otherwise
        """
        if self.backend == "sqlite":
            return self._load_sqlite(session_id, call_hash, ttl)
        else:
            return self._load_json(session_id, call_hash)
    
    def _load_sqlite(self, session_id: str, call_hash: str, ttl: Optional[int]) -> Optional[Dict[str, Any]]:
        """
        Load from SQLite database.
        
        Args:
            session_id: Session identifier
            call_hash: Call hash
            ttl: Time-to-live in seconds
            
        Returns:
            Recording data if found and not expired, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT data, timestamp FROM recordings WHERE session_id = ? AND call_hash = ?",
            (session_id, call_hash)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        data, timestamp = row
        
        # Check TTL
        if ttl and (time.time() - timestamp) > ttl:
            return None
        
        return json.loads(data)
    
    def _load_json(self, session_id: str, call_hash: str) -> Optional[Dict[str, Any]]:
        """
        Load from JSON file.
        
        Args:
            session_id: Session identifier
            call_hash: Call hash
            
        Returns:
            Recording data if found, None otherwise
        """
        file_path = os.path.join(self.save_dir, f"{session_id}.json")
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r') as f:
            recordings = json.load(f)
        
        return recordings.get(call_hash)
    
    def clear(self, session_id: Optional[str] = None) -> None:
        """
        Clear cached recordings.
        
        Args:
            session_id: Specific session to clear (None = clear all sessions)
        """
        if self.backend == "sqlite":
            conn = sqlite3.connect(self.db_path)
            if session_id:
                conn.execute("DELETE FROM recordings WHERE session_id = ?", (session_id,))
            else:
                conn.execute("DELETE FROM recordings")
            conn.commit()
            conn.close()
        else:
            if session_id:
                file_path = os.path.join(self.save_dir, f"{session_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
            else:
                for file in os.listdir(self.save_dir):
                    if file.endswith(".json"):
                        os.remove(os.path.join(self.save_dir, file))
    
    def get_all_sessions(self) -> List[str]:
        """
        Get list of all session IDs.
        
        Returns:
            List of unique session identifiers
        """
        if self.backend == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT DISTINCT session_id FROM recordings")
            sessions = [row[0] for row in cursor.fetchall()]
            conn.close()
            return sessions
        else:
            return [f.replace(".json", "") for f in os.listdir(self.save_dir) if f.endswith(".json")]

    def get_session_calls(self, session_id: str) -> Dict[str, Any]:
        """
        Get all calls for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary mapping call hashes to recording data
        """
        if self.backend == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT call_hash, data, cost FROM recordings WHERE session_id = ?",
                (session_id,)
            )
            results = {}
            for row in cursor.fetchall():
                call_hash, data, cost = row
                parsed_data = json.loads(data)
                parsed_data['cost'] = cost
                results[call_hash] = parsed_data
            conn.close()
            return results
        else:
            file_path = os.path.join(self.save_dir, f"{session_id}.json")
            if not os.path.exists(file_path):
                return {}
            with open(file_path, 'r') as f:
                return json.load(f)