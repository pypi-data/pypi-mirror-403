"""
Unit tests for the recorder.
"""

import unittest
import os
import shutil
from agent_flight_recorder import Recorder


class TestRecorder(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = "./test_afr_logs"
        self.recorder = Recorder(save_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_basic_recording(self):
        """Test basic record and replay."""
        
        @self.recorder.trace(session_id="test_session")
        def add(a, b):
            return a + b
        
        # First call - should record
        result1 = add(2, 3)
        self.assertEqual(result1, 5)
        
        # Second call - should replay
        result2 = add(2, 3)
        self.assertEqual(result2, 5)
    
    def test_different_inputs(self):
        """Test that different inputs create different recordings."""
        
        @self.recorder.trace(session_id="test_inputs")
        def multiply(a, b):
            return a * b
        
        result1 = multiply(2, 3)
        result2 = multiply(4, 5)
        
        self.assertEqual(result1, 6)
        self.assertEqual(result2, 20)
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        
        @self.recorder.trace(session_id="test_clear")
        def subtract(a, b):
            return a - b
        
        subtract(10, 5)
        self.recorder.clear("test_clear")
        
        # After clearing, should record again
        subtract(10, 5)


if __name__ == "__main__":
    unittest.main()

