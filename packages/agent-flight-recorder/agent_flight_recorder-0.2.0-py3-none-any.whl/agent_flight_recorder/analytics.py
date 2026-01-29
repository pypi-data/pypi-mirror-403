
"""
Analytics and cost tracking for Agent Flight Recorder.

This module tracks API call statistics, cost savings, and provides
detailed analytics about recording and replay performance.
"""

import sqlite3
import logging
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .storage import Storage

logger = logging.getLogger(__name__)


class Analytics:
    """
    Track costs and statistics for AI API calls.
    
    Maintains statistics about live calls, replayed calls, and cost savings.
    """
    
    def __init__(self, storage: "Storage") -> None:
        """
        Initialize analytics tracker.
        
        Args:
            storage: Storage backend instance
        """
        self.storage = storage
        self.stats: Dict[str, Any] = {
            "live_calls": 0,
            "replayed_calls": 0,
            "total_cost": 0,
            "cost_saved": 0
        }
    
    def record_live_call(self, session_id: str, call_hash: str, cost: float) -> None:
        """
        Record a live API call.
        
        Args:
            session_id: Session identifier
            call_hash: Unique call hash
            cost: Cost of the API call
        """
        self.stats["live_calls"] += 1
        self.stats["total_cost"] += cost
    
    def record_replay(self, session_id: str, call_hash: str) -> None:
        """
        Record a replayed call (cache hit).
        
        Args:
            session_id: Session identifier
            call_hash: Unique call hash
        """
        self.stats["replayed_calls"] += 1
        
        # Try to get cost of original call
        if self.storage.backend == "sqlite":
            conn = sqlite3.connect(self.storage.db_path)
            cursor = conn.execute(
                "SELECT cost FROM recordings WHERE session_id = ? AND call_hash = ?",
                (session_id, call_hash)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0]:
                self.stats["cost_saved"] += row[0]
    
    def display_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Display analytics summary.
        
        Args:
            session_id: Optional session to filter by
            
        Returns:
            Dictionary containing statistics
        """
        print("\n" + "="*50)
        print("📊 AGENT FLIGHT RECORDER STATISTICS")
        print("="*50)
        
        if session_id:
            print(f"Session: {session_id}")
        
        print(f"\n💰 Cost Saved: ${self.stats['cost_saved']:.4f}")
        print(f"📈 Total Cost Spent: ${self.stats['total_cost']:.4f}")
        print(f"🔴 Live API Calls: {self.stats['live_calls']}")
        print(f"✈️  Replayed Calls: {self.stats['replayed_calls']}")
        
        if self.stats['live_calls'] > 0:
            total_calls = self.stats['live_calls'] + self.stats['replayed_calls']
            replay_percent = (self.stats['replayed_calls'] / total_calls) * 100
            print(f"⚡ Replay Rate: {replay_percent:.1f}%")
        
        print("="*50 + "\n")
        
        return self.stats
    
    def diff_sessions(self, session_id_1: str, session_id_2: str) -> None:
        """
        Compare two recording sessions.
        
        Shows differences in total calls, costs, and common vs unique calls.
        Displays detailed analysis of:
        - Total calls and costs
        - Unique calls in each session
        - Common calls between sessions
        - Cost difference
        - Efficiency metrics
        
        Args:
            session_id_1: First session to compare
            session_id_2: Second session to compare
        """
        calls1 = self.storage.get_session_calls(session_id_1)
        calls2 = self.storage.get_session_calls(session_id_2)
        
        cost1 = sum(c.get('cost', 0) for c in calls1.values())
        cost2 = sum(c.get('cost', 0) for c in calls2.values())
        
        print(f"\n🔍 DETAILED SESSION COMPARISON")
        print(f"   {session_id_1} vs {session_id_2}")
        print("="*70)
        
        # Basic metrics
        print(f"\n📊 Basic Metrics:")
        print(f"{'Metric':<25} | {session_id_1:<20} | {session_id_2:<20}")
        print("-" * 70)
        print(f"{'Total Calls':<25} | {len(calls1):<20} | {len(calls2):<20}")
        print(f"{'Total Cost':<25} | ${cost1:<19.4f} | ${cost2:<19.4f}")
        
        # Find unique and common calls
        hashes1 = set(calls1.keys())
        hashes2 = set(calls2.keys())
        
        unique1 = hashes1 - hashes2
        unique2 = hashes2 - hashes1
        common = hashes1 & hashes2
        
        print(f"\n📈 Call Distribution:")
        print(f"{'Unique to ' + session_id_1:<25} | {len(unique1):<20}")
        print(f"{'Unique to ' + session_id_2:<25} | {len(unique2):<20}")
        print(f"{'Common Calls':<25} | {len(common):<20}")
        
        # Cost analysis
        if len(common) > 0:
            common_cost1 = sum(calls1[h].get('cost', 0) for h in common)
            common_cost2 = sum(calls2[h].get('cost', 0) for h in common)
            print(f"\n💰 Cost Analysis:")
            print(f"{'Cost for Common Calls':<25} | ${common_cost1:<19.4f} | ${common_cost2:<19.4f}")
            print(f"{'Cost for Unique Calls':<25} | ${(cost1 - common_cost1):<19.4f} | ${(cost2 - common_cost2):<19.4f}")
        
        # Efficiency metrics
        if len(calls1) > 0 and len(calls2) > 0:
            overlap_percent = (len(common) / max(len(calls1), len(calls2))) * 100
            print(f"\n⚡ Efficiency Metrics:")
            print(f"{'Call Overlap':<25} | {overlap_percent:.1f}%")
            
            if cost1 > 0 and cost2 > 0:
                cost_diff = abs(cost1 - cost2)
                cost_diff_percent = (cost_diff / max(cost1, cost2)) * 100
                print(f"{'Cost Difference':<25} | ${cost_diff:.4f} ({cost_diff_percent:.1f}%)")
        
        print("="*70 + "\n")