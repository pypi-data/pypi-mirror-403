
"""
Interceptors for AI API providers (OpenAI, Anthropic).

This module provides monkey-patched interceptors to transparently
record and replay API calls from various AI service providers.
"""

import functools
import logging
from typing import Any, Optional, Dict, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .storage import Storage
    from .analytics import Analytics

logger = logging.getLogger(__name__)

class BaseInterceptor:
    """
    Base class for API interceptors.
    
    Provides common interface for intercepting and modifying API calls
    from various AI service providers.
    """
    
    def __init__(self, storage: "Storage", analytics: "Analytics") -> None:
        """
        Initialize the interceptor.
        
        Args:
            storage: Storage backend for caching
            analytics: Analytics tracker
        """
        self.storage = storage
        self.analytics = analytics
        self.original_methods: Dict[str, Any] = {}
    
    def activate(self) -> None:
        """Activate the interceptor (monkey-patch the API)."""
        raise NotImplementedError
    
    def deactivate(self) -> None:
        """Restore original API methods."""
        raise NotImplementedError


class OpenAIInterceptor(BaseInterceptor):
    """
    Intercepts OpenAI API calls for recording and replay.
    
    Monkey-patches the ChatCompletion.create method to transparently
    record responses and replay them on subsequent identical calls.
    """
    
    def activate(self) -> None:
        """Patch OpenAI's ChatCompletion.create method."""
        try:
            import openai
            
            # Store original method
            if hasattr(openai.ChatCompletion, 'create'):
                self.original_methods['chat_completion'] = openai.ChatCompletion.create
                
                # Create wrapper
                @functools.wraps(openai.ChatCompletion.create)
                def wrapped_create(*args, **kwargs):
                    # Generate hash
                    call_hash = self.storage.create_hash(args, kwargs, "openai_v1")
                    session_id = kwargs.get('session_id', 'default_openai_session')
                    
                    # Remove our custom param
                    kwargs.pop('session_id', None)
                    
                    # Try to load from cache
                    cached = self.storage.load(session_id, call_hash)
                    if cached:
                        logger.info("✈️  [REPLAY] Using cached OpenAI response")
                        self.analytics.record_replay(session_id, call_hash)
                        return cached['output']
                    
                    # Make actual API call
                    logger.info("🔴 [RECORD] Calling OpenAI API...")
                    result = self.original_methods['chat_completion'](*args, **kwargs)
                    
                    # Calculate cost (rough estimate)
                    cost = self._estimate_cost(kwargs.get('model', 'gpt-3.5-turbo'), result)
                    
                    # Save to storage
                    self.storage.save(
                        session_id=session_id,
                        call_hash=call_hash,
                        data={
                            "provider": "openai",
                            "input": {"args": args, "kwargs": kwargs},
                            "output": result
                        },
                        cost=cost
                    )
                    
                    self.analytics.record_live_call(session_id, call_hash, cost)
                    
                    return result
                
                # Apply patch
                openai.ChatCompletion.create = wrapped_create
                logger.info("✅ OpenAI interceptor activated")
        
        except ImportError:
            logger.warning("⚠️  OpenAI not installed, skipping interceptor")
    
    def _estimate_cost(self, model: str, result: Any) -> float:
        """
        Estimate API call cost based on model and tokens used.
        
        Uses standard OpenAI pricing rates for different model tiers.
        
        Args:
            model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
            result: API response object
            
        Returns:
            Estimated cost in dollars
        """
        try:
            usage = result.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            
            # Pricing per 1K tokens (as of 2024)
            pricing = {
                'gpt-4': (0.03, 0.06),
                'gpt-4-turbo': (0.01, 0.03),
                'gpt-3.5-turbo': (0.0015, 0.002),
            }
            
            for model_name, (input_price, output_price) in pricing.items():
                if model_name in model:
                    return (prompt_tokens / 1000 * input_price) + (completion_tokens / 1000 * output_price)
            
            return 0
        except:
            return 0
    
    def deactivate(self) -> None:
        """Restore original OpenAI methods."""
        try:
            import openai
            if 'chat_completion' in self.original_methods:
                openai.ChatCompletion.create = self.original_methods['chat_completion']
                logger.info("✅ OpenAI interceptor deactivated")
        except ImportError:
            pass


class AnthropicInterceptor(BaseInterceptor):
    """
    Intercepts Anthropic API calls for recording and replay.
    
    Monkey-patches the Anthropic client to transparently record
    responses and replay them on subsequent identical calls.
    """
    
    def activate(self) -> None:
        """Patch Anthropic's messages.create method."""
        try:
            import anthropic
            
            # Store reference to interceptor instance
            storage = self.storage
            analytics = self.analytics
            
            # Store original method
            original_client_init = anthropic.Anthropic.__init__
            self.original_methods['client_init'] = original_client_init
            
            def patched_init(client_self, *args, **kwargs):
                original_client_init(client_self, *args, **kwargs)
                
                # Wrap the messages.create method
                original_create = client_self.messages.create
                
                @functools.wraps(original_create)
                def wrapped_create(*args, **kwargs):
                    call_hash = storage.create_hash(args, kwargs, "anthropic_v1")
                    session_id = kwargs.get('session_id', 'default_anthropic_session')
                    kwargs.pop('session_id', None)
                    
                    # Try cache
                    cached = storage.load(session_id, call_hash)
                    if cached:
                        logger.info("✈️  [REPLAY] Using cached Anthropic response")
                        analytics.record_replay(session_id, call_hash)
                        return cached['output']
                    
                    # Make actual call
                    logger.info("🔴 [RECORD] Calling Anthropic API...")
                    result = original_create(*args, **kwargs)
                    
                    # Calculate cost estimate
                    cost = 0
                    try:
                        usage = getattr(result, 'usage', None)
                        if usage:
                            input_tokens = getattr(usage, 'input_tokens', 0)
                            output_tokens = getattr(usage, 'output_tokens', 0)
                            # Rough pricing estimate (Claude 3)
                            cost = (input_tokens / 1000 * 0.003) + (output_tokens / 1000 * 0.015)
                    except:
                        pass
                    
                    # Save
                    storage.save(
                        session_id=session_id,
                        call_hash=call_hash,
                        data={
                            "provider": "anthropic",
                            "input": {"args": args, "kwargs": kwargs},
                            "output": result
                        },
                        cost=cost
                    )
                    
                    analytics.record_live_call(session_id, call_hash, cost)
                    
                    return result
                
                client_self.messages.create = wrapped_create
            
            anthropic.Anthropic.__init__ = patched_init
            logger.info("✅ Anthropic interceptor activated")
        
        except ImportError:
            logger.warning("⚠️  Anthropic not installed, skipping interceptor")
    
    def deactivate(self) -> None:
        """Restore original Anthropic methods."""
        try:
            import anthropic
            if 'client_init' in self.original_methods:
                anthropic.Anthropic.__init__ = self.original_methods['client_init']
                logger.info("✅ Anthropic interceptor deactivated")
        except ImportError:
            pass