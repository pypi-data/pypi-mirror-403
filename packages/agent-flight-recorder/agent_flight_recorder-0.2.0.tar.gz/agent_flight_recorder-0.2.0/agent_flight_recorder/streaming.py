"""
Streaming response support for Agent Flight Recorder.

Handles recording and replaying of streaming API responses
from providers like OpenAI (with stream=True) and Anthropic.
"""

import logging
import json
from typing import Any, Iterator, Optional, Dict, List

logger = logging.getLogger(__name__)


class StreamRecorder:
    """Records and replays streaming API responses."""
    
    def __init__(self, storage: "Storage") -> None:
        """
        Initialize the stream recorder.
        
        Args:
            storage: Storage backend for caching streams
        """
        self.storage = storage
    
    def record_stream(
        self, 
        stream_iterator: Iterator[Any], 
        session_id: str,
        call_hash: str,
        provider: str
    ) -> Iterator[Any]:
        """
        Record a streaming response while yielding chunks.
        
        Buffers chunks from the stream and saves them when complete.
        
        Args:
            stream_iterator: Original streaming iterator
            session_id: Session identifier
            call_hash: Call hash
            provider: Provider name (e.g., 'openai')
            
        Yields:
            Stream chunks
        """
        chunks: List[Dict[str, Any]] = []
        
        try:
            for chunk in stream_iterator:
                # Buffer the chunk
                try:
                    chunk_data = chunk.model_dump() if hasattr(chunk, 'model_dump') else chunk
                    chunks.append(chunk_data)
                except:
                    chunks.append(chunk)
                
                # Yield immediately
                yield chunk
            
            # Save complete stream
            self.storage.save(
                session_id=session_id,
                call_hash=call_hash,
                data={
                    "provider": provider,
                    "stream": True,
                    "chunks": chunks,
                    "chunk_count": len(chunks)
                }
            )
            
            logger.info(f"✈️  [RECORD_STREAM] Recorded {len(chunks)} chunks")
        
        except Exception as e:
            logger.error(f"Error recording stream: {e}")
            raise
    
    def replay_stream(
        self, 
        session_id: str, 
        call_hash: str
    ) -> Optional[Iterator[Any]]:
        """
        Replay a cached streaming response.
        
        Args:
            session_id: Session identifier
            call_hash: Call hash
            
        Returns:
            Iterator of chunks if found, None otherwise
        """
        cached = self.storage.load(session_id, call_hash)
        
        if cached is None or not cached.get("stream"):
            return None
        
        chunks = cached.get("chunks", [])
        logger.info(f"✈️  [REPLAY_STREAM] Replaying {len(chunks)} cached chunks")
        
        def chunk_iterator():
            """Yield cached chunks."""
            for chunk in chunks:
                yield chunk
        
        return chunk_iterator()
    
    def is_streaming_response(self, response: Any) -> bool:
        """
        Check if a response is a streaming response.
        
        Args:
            response: Response object to check
            
        Returns:
            True if response is streaming, False otherwise
        """
        # Check for OpenAI streaming
        if hasattr(response, '__iter__') and not isinstance(response, (str, dict)):
            # Exclude iterators that are clearly not streams
            if hasattr(response, '__name__') and 'stream' in str(response.__name__).lower():
                return True
        
        return False
    
    def buffer_stream_to_completion(
        self, 
        stream_iterator: Iterator[Any]
    ) -> Dict[str, Any]:
        """
        Buffer a stream until completion and construct full response.
        
        Useful for converting streams to standard responses.
        
        Args:
            stream_iterator: Streaming iterator
            
        Returns:
            Reconstructed response object
        """
        chunks: List[Dict[str, Any]] = []
        full_text = ""
        
        for chunk in stream_iterator:
            try:
                chunk_data = chunk.model_dump() if hasattr(chunk, 'model_dump') else chunk
                chunks.append(chunk_data)
                
                # Extract text if available
                if isinstance(chunk_data, dict):
                    choices = chunk_data.get('choices', [])
                    if choices and len(choices) > 0:
                        delta = choices[0].get('delta', {})
                        if isinstance(delta, dict) and 'content' in delta:
                            full_text += delta['content']
            except:
                chunks.append(chunk)
        
        return {
            "chunks": chunks,
            "full_text": full_text,
            "chunk_count": len(chunks)
        }
