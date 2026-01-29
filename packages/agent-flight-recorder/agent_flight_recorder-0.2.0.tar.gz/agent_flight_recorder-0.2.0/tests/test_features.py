"""
Test suite for Agent Flight Recorder - Streaming, Filtering, and Providers.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock

from agent_flight_recorder.streaming import StreamRecorder
from agent_flight_recorder.filtering import DataFilter
from agent_flight_recorder.storage import Storage


class TestStreamRecorder:
    """Tests for streaming response handling."""
    
    @pytest.fixture
    def storage(self):
        """Create a temporary storage instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Storage(tmpdir, backend="sqlite")
    
    @pytest.fixture
    def stream_recorder(self, storage):
        """Create a StreamRecorder instance."""
        return StreamRecorder(storage)
    
    def test_record_stream(self, stream_recorder, storage):
        """Test recording a stream."""
        chunks = [{"choice": i} for i in range(5)]
        
        def stream_iterator():
            for chunk in chunks:
                yield chunk
        
        recorded_chunks = list(stream_recorder.record_stream(
            stream_iterator(),
            session_id="test",
            call_hash="hash123",
            provider="test_provider"
        ))
        
        assert len(recorded_chunks) == 5
        assert recorded_chunks == chunks
    
    def test_replay_stream(self, stream_recorder, storage):
        """Test replaying a stream."""
        # Save a stream first
        storage.save(
            session_id="test",
            call_hash="hash123",
            data={
                "provider": "test",
                "stream": True,
                "chunks": [{"data": 1}, {"data": 2}]
            }
        )
        
        # Replay it
        replayed = stream_recorder.replay_stream("test", "hash123")
        assert replayed is not None
        replayed_chunks = list(replayed)
        assert len(replayed_chunks) == 2
    
    def test_buffer_stream_to_completion(self, stream_recorder):
        """Test buffering a stream to completion."""
        def stream_iterator():
            yield {"choices": [{"delta": {"content": "Hello "}}]}
            yield {"choices": [{"delta": {"content": "World"}}]}
            yield {"choices": [{"delta": {"content": "!"}}]}
        
        result = stream_recorder.buffer_stream_to_completion(stream_iterator())
        
        assert result["full_text"] == "Hello World!"
        assert result["chunk_count"] == 3


class TestDataFilter:
    """Tests for request/response filtering."""
    
    @pytest.fixture
    def data_filter(self):
        """Create a DataFilter instance."""
        return DataFilter()
    
    def test_redact_api_key(self, data_filter):
        """Test redacting API keys."""
        data = {
            "api_key": "sk-12345",
            "user": "john"
        }
        
        filtered = data_filter.filter_data(data)
        
        assert filtered["api_key"] == "[REDACTED_API_KEY]"
        assert filtered["user"] == "john"
    
    def test_redact_authorization(self, data_filter):
        """Test redacting authorization headers."""
        data = {
            "Authorization": "Bearer token123",
            "Content-Type": "application/json"
        }
        
        filtered = data_filter.filter_data(data)
        
        assert filtered["Authorization"] == "[REDACTED_AUTH]"
        assert filtered["Content-Type"] == "application/json"
    
    def test_redact_nested_data(self, data_filter):
        """Test redacting nested structures."""
        data = {
            "user": {
                "name": "John",
                "api_key": "secret123"
            },
            "tokens": ["token1", "token2"]
        }
        
        filtered = data_filter.filter_data(data)
        
        assert filtered["user"]["name"] == "John"
        assert filtered["user"]["api_key"] == "[REDACTED_API_KEY]"
    
    def test_filter_fields_whitelist(self, data_filter):
        """Test filtering to whitelist fields."""
        data = {
            "id": "123",
            "name": "John",
            "email": "john@example.com",
            "password": "secret"
        }
        
        filtered = data_filter.filter_fields(
            data, 
            allowed_fields=["id", "name"]
        )
        
        assert "id" in filtered
        assert "name" in filtered
        assert "email" not in filtered
        assert "password" not in filtered
    
    def test_filter_fields_blacklist(self, data_filter):
        """Test filtering to exclude fields."""
        data = {
            "id": "123",
            "name": "John",
            "email": "john@example.com",
            "password": "secret"
        }
        
        filtered = data_filter.filter_fields(
            data,
            excluded_fields=["password", "email"]
        )
        
        assert "id" in filtered
        assert "name" in filtered
        assert "email" not in filtered
        assert "password" not in filtered
    
    def test_add_custom_filter(self, data_filter):
        """Test adding custom filter functions."""
        def uppercase_names(data):
            if isinstance(data, dict) and "name" in data:
                data["name"] = data["name"].upper()
            return data
        
        data_filter.add_custom_filter(uppercase_names)
        filtered = data_filter.filter_data({"name": "john", "age": 30})
        
        assert filtered["name"] == "JOHN"
        assert filtered["age"] == 30
    
    def test_filter_large_responses(self, data_filter):
        """Test truncating large responses."""
        large_data = {"text": "x" * (1024 * 200)}  # 200 KB
        
        filtered = data_filter.filter_large_responses(
            large_data,
            max_size_bytes=1024 * 100  # 100 KB limit
        )
        
        assert filtered["__truncated__"] is True
        assert filtered["original_size"] > 1024 * 100


class TestRecorderIntegration:
    """Integration tests for recorder with new features."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_recorder_with_filtering(self, temp_dir):
        """Test recorder with data filtering."""
        from agent_flight_recorder import Recorder, DataFilter
        
        recorder = Recorder(save_dir=temp_dir)
        data_filter = DataFilter()
        
        @recorder.trace(session_id="filtered_test")
        def api_call(api_key):
            return {"result": "success", "key": api_key}
        
        # First call
        result = api_call("sk-secret123")
        assert result["key"] == "sk-secret123"
        
        # Second call (replayed)
        result2 = api_call("sk-secret123")
        assert result2 == result  # Should be identical even with different key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
