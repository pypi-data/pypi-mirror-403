
"""
Core recording and replay functionality for Agent Flight Recorder.

This module provides the main Recorder class that handles tracing,
caching, and replaying of expensive function calls and API requests.
"""

import functools
import logging
import os
import traceback
from typing import Any, Callable, Optional, List

from .storage import Storage
from .interceptors import OpenAIInterceptor, AnthropicInterceptor
from .analytics import Analytics

logger = logging.getLogger(__name__)

class Recorder:
    """
    Main class for recording and replaying AI agent interactions.
    
    Records expensive function outputs and API responses, allowing
    subsequent identical calls to be replayed from cache without
    incurring additional API costs.
    
    Example:
        recorder = Recorder(save_dir="./logs")
        
        @recorder.trace(session_id="test_1")
        def my_ai_function(prompt):
            return openai.ChatCompletion.create(...)
    """
    
    def __init__(
        self,
        save_dir: str = "./afr_logs",
        mode: str = "auto",
        providers: Optional[List[str]] = None,
        storage_backend: str = "sqlite"
    ) -> None:
        """
        Initialize the recorder.
        
        Args:
            save_dir: Directory to save recordings
            mode: Recording mode - "auto" (record then replay), 
                  "record-only", or "replay-only"
            providers: List of API providers to intercept 
                      (["openai", "anthropic"])
            storage_backend: Storage backend - "json" or "sqlite" 
                           (default: sqlite for performance)
        """
        self.save_dir = save_dir
        self.mode = mode
        self.storage = Storage(save_dir, backend=storage_backend)
        self.analytics = Analytics(self.storage)
        self.interceptors: List[Any] = []
        # Create logs directory
        os.makedirs(save_dir, exist_ok=True)
        
        # Initialize interceptors
        self.interceptors = []
        if providers:
            if "openai" in providers:
                self.interceptors.append(OpenAIInterceptor(self.storage, self.analytics))
            if "anthropic" in providers:
                self.interceptors.append(AnthropicInterceptor(self.storage, self.analytics))
        
        # Activate interceptors
        for interceptor in self.interceptors:
            interceptor.activate()
    
    def trace(self, session_id: str, ttl: Optional[int] = None, version: str = "v1") -> Callable:
        """
        Decorator to trace function calls and enable caching.
        
        Creates a unique hash of the function inputs and uses it to
        check the cache before executing the function. If a cached
        result exists, returns it immediately. Otherwise, executes
        the function and caches the result.
        
        Args:
            session_id: Unique identifier for this recording session
            ttl: Time-to-live in seconds (None = never expire)
            version: Version string to invalidate old caches
        
        Returns:
            Decorator function
        
        Example:
            @recorder.trace(session_id="my_test", ttl=3600, version="v2")
            def expensive_function(prompt):
                return call_expensive_api(prompt)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Create unique hash for this call
                call_hash = self.storage.create_hash(args, kwargs, version)
                
                # Try to load from storage (REPLAY MODE)
                if self.mode in ["auto", "replay-only"]:
                    cached = self.storage.load(session_id, call_hash, ttl)
                    if cached is not None:
                        logger.info(f"✈️  [REPLAY] Loaded cached result for {func.__name__}")
                        self.analytics.record_replay(session_id, call_hash)
                        
                        # Handle cached errors
                        if "error" in cached:
                            raise Exception(f"Replayed error: {cached['error']}")
                        
                        return cached["output"]
                
                # Check if we're in replay-only mode and have no cache
                if self.mode == "replay-only":
                    raise ValueError(
                        f"No cached result found for {func.__name__} "
                        f"and mode is set to 'replay-only'"
                    )
                
                # Execute function (RECORD MODE)
                logger.info(f"🔴 [RECORD] Running live function: {func.__name__}...")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Save successful result
                    self.storage.save(
                        session_id=session_id,
                        call_hash=call_hash,
                        data={
                            "function": func.__name__,
                            "input": {"args": args, "kwargs": kwargs},
                            "output": result,
                            "version": version
                        }
                    )
                    
                    self.analytics.record_live_call(session_id, call_hash, cost=0)
                    
                    return result
                
                except Exception as e:
                    # Save error for replay
                    self.storage.save(
                        session_id=session_id,
                        call_hash=call_hash,
                        data={
                            "function": func.__name__,
                            "input": {"args": args, "kwargs": kwargs},
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                            "version": version
                        }
                    )
                    raise
            
            return wrapper
        return decorator
    
    def stats(self, session_id: Optional[str] = None) -> Any:
        """
        Display analytics and cost savings.
        
        Args:
            session_id: Filter stats by session (None = all sessions)
            
        Returns:
            Statistics dictionary
        """
        return self.analytics.display_stats(session_id)
    
    def diff(self, session_id_1: str, session_id_2: str) -> None:
        """
        Compare two recording sessions.
        
        Args:
            session_id_1: First session to compare
            session_id_2: Second session to compare
        """
        return self.analytics.diff_sessions(session_id_1, session_id_2)
    
    def clear(self, session_id: Optional[str] = None) -> None:
        """
        Clear cached recordings.
        
        Args:
            session_id: Clear specific session (None = clear all)
        """
        self.storage.clear(session_id)
        logger.info(f"🗑️  Cleared recordings" + (f" for session: {session_id}" if session_id else ""))
    
    def deactivate(self) -> None:
        """Deactivate all interceptors."""
        for interceptor in self.interceptors:
            interceptor.deactivate()