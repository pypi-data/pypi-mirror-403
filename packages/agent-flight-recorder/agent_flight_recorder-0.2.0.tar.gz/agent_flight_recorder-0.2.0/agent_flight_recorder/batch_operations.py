"""
Batch operations for Agent Flight Recorder.

Provides bulk operations for managing multiple recordings,
exporting/importing sessions, and batch processing.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BatchOperations:
    """Handle batch operations on recordings."""
    
    def __init__(self, storage: "Storage") -> None:
        """
        Initialize batch operations.
        
        Args:
            storage: Storage backend instance
        """
        self.storage = storage
    
    def export_session(
        self, 
        session_id: str, 
        output_path: str,
        format: str = "json"
    ) -> None:
        """
        Export a session to a file.
        
        Args:
            session_id: Session to export
            output_path: Path to write export file
            format: Export format ("json" or "csv")
        """
        calls = self.storage.get_session_calls(session_id)
        
        if format == "json":
            self._export_json(session_id, calls, output_path)
        elif format == "csv":
            self._export_csv(session_id, calls, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"✅ Exported session {session_id} to {output_path}")
    
    def _export_json(
        self, 
        session_id: str, 
        calls: Dict[str, Any], 
        output_path: str
    ) -> None:
        """Export session as JSON."""
        export_data = {
            "session_id": session_id,
            "export_timestamp": datetime.now().isoformat(),
            "call_count": len(calls),
            "calls": calls
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def _export_csv(
        self, 
        session_id: str, 
        calls: Dict[str, Any], 
        output_path: str
    ) -> None:
        """Export session as CSV."""
        try:
            import csv
        except ImportError:
            raise ImportError("csv module not available")
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "call_hash",
                "function",
                "status",
                "cost",
                "timestamp"
            ])
            
            # Rows
            for call_hash, data in calls.items():
                writer.writerow([
                    call_hash,
                    data.get("function", "unknown"),
                    "success" if "output" in data else "error",
                    data.get("cost", 0),
                    data.get("timestamp", "")
                ])
    
    def import_session(
        self, 
        import_path: str, 
        session_id: Optional[str] = None
    ) -> str:
        """
        Import a session from a file.
        
        Args:
            import_path: Path to import file
            session_id: Override session ID (uses exported ID if None)
            
        Returns:
            Imported session ID
        """
        with open(import_path, 'r') as f:
            data = json.load(f)
        
        imported_session_id = session_id or data.get("session_id", "imported")
        calls = data.get("calls", {})
        
        # Import calls
        for call_hash, call_data in calls.items():
            self.storage.save(
                session_id=imported_session_id,
                call_hash=call_hash,
                data=call_data,
                cost=call_data.get("cost", 0)
            )
        
        logger.info(f"✅ Imported {len(calls)} calls to session {imported_session_id}")
        return imported_session_id
    
    def merge_sessions(
        self, 
        session_ids: List[str], 
        new_session_id: str
    ) -> None:
        """
        Merge multiple sessions into one.
        
        Args:
            session_ids: Sessions to merge
            new_session_id: New merged session ID
        """
        total_calls = 0
        
        for session_id in session_ids:
            calls = self.storage.get_session_calls(session_id)
            
            for call_hash, data in calls.items():
                self.storage.save(
                    session_id=new_session_id,
                    call_hash=call_hash,
                    data=data,
                    cost=data.get("cost", 0)
                )
                total_calls += 1
        
        logger.info(f"✅ Merged {len(session_ids)} sessions into {new_session_id} "
                   f"({total_calls} calls)")
    
    def prune_sessions(
        self, 
        max_age_days: Optional[int] = None,
        min_cost_saved: Optional[float] = None
    ) -> int:
        """
        Prune old or low-value sessions.
        
        Args:
            max_age_days: Remove sessions older than this many days
            min_cost_saved: Remove sessions with less cost saved
            
        Returns:
            Number of sessions pruned
        """
        # This is a placeholder - full implementation would need timestamp tracking
        pruned = 0
        
        if max_age_days:
            logger.info(f"⏰ Would prune sessions older than {max_age_days} days")
        
        if min_cost_saved:
            logger.info(f"💰 Would prune sessions with <${min_cost_saved} savings")
        
        return pruned
    
    def duplicate_session(
        self, 
        source_session_id: str, 
        new_session_id: str
    ) -> None:
        """
        Create a copy of a session.
        
        Args:
            source_session_id: Session to copy
            new_session_id: New session ID
        """
        calls = self.storage.get_session_calls(source_session_id)
        
        for call_hash, data in calls.items():
            self.storage.save(
                session_id=new_session_id,
                call_hash=call_hash,
                data=data.copy(),
                cost=data.get("cost", 0)
            )
        
        logger.info(f"✅ Duplicated session {source_session_id} to {new_session_id}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a session.
        
        Args:
            session_id: Session to summarize
            
        Returns:
            Dictionary with summary stats
        """
        calls = self.storage.get_session_calls(session_id)
        
        total_cost = sum(c.get("cost", 0) for c in calls.values())
        error_count = sum(1 for c in calls.values() if "error" in c)
        success_count = len(calls) - error_count
        
        return {
            "session_id": session_id,
            "total_calls": len(calls),
            "success_calls": success_count,
            "error_calls": error_count,
            "total_cost": total_cost,
            "success_rate": (success_count / len(calls) * 100) if calls else 0
        }
    
    def bulk_delete_by_pattern(
        self, 
        session_pattern: str
    ) -> int:
        """
        Delete sessions matching a pattern.
        
        Args:
            session_pattern: Regex pattern to match session IDs
            
        Returns:
            Number of sessions deleted
        """
        import re
        
        sessions = self.storage.get_all_sessions()
        pattern = re.compile(session_pattern)
        
        deleted = 0
        for session_id in sessions:
            if pattern.match(session_id):
                self.storage.clear(session_id)
                deleted += 1
        
        logger.info(f"🗑️  Deleted {deleted} sessions matching pattern '{session_pattern}'")
        return deleted
