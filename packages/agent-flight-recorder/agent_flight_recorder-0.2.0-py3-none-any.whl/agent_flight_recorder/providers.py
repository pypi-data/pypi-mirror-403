"""
Additional provider integrations for Agent Flight Recorder.

Supports Google Vertex AI, Cohere, and other AI service providers.
"""

import functools
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


class GoogleVertexAIInterceptor:
    """
    Intercepts Google Vertex AI API calls.
    
    Records and replays requests to Google's generative AI services
    including PaLM 2, Gemini, and other models.
    """
    
    def __init__(self, storage: "Storage", analytics: "Analytics") -> None:
        """
        Initialize the Google Vertex AI interceptor.
        
        Args:
            storage: Storage backend
            analytics: Analytics tracker
        """
        self.storage = storage
        self.analytics = analytics
        self.original_methods: Dict[str, Any] = {}
    
    def activate(self) -> None:
        """Patch Google Vertex AI methods."""
        try:
            import google.generativeai as genai
            
            # Store original
            self.original_methods['generate_content'] = genai.GenerativeModel.generate_content
            
            # Create wrapper
            @functools.wraps(genai.GenerativeModel.generate_content)
            def wrapped_generate(model_self, *args, **kwargs):
                call_hash = self.storage.create_hash(args, kwargs, "google_v1")
                session_id = kwargs.pop('session_id', 'default_google_session')
                
                # Try cache
                cached = self.storage.load(session_id, call_hash)
                if cached:
                    logger.info("✈️  [REPLAY] Using cached Google response")
                    self.analytics.record_replay(session_id, call_hash)
                    return cached['output']
                
                # Execute
                logger.info("🔴 [RECORD] Calling Google Vertex AI...")
                result = self.original_methods['generate_content'](model_self, *args, **kwargs)
                
                # Save
                self.storage.save(
                    session_id=session_id,
                    call_hash=call_hash,
                    data={
                        "provider": "google_vertex_ai",
                        "input": {"args": args, "kwargs": kwargs},
                        "output": result
                    },
                    cost=0  # Google pricing varies
                )
                
                self.analytics.record_live_call(session_id, call_hash, cost=0)
                return result
            
            genai.GenerativeModel.generate_content = wrapped_generate
            logger.info("✅ Google Vertex AI interceptor activated")
        
        except ImportError:
            logger.warning("⚠️  google-generativeai not installed, skipping interceptor")
    
    def deactivate(self) -> None:
        """Restore original Google methods."""
        try:
            import google.generativeai as genai
            if 'generate_content' in self.original_methods:
                genai.GenerativeModel.generate_content = self.original_methods['generate_content']
                logger.info("✅ Google Vertex AI interceptor deactivated")
        except ImportError:
            pass


class CohereInterceptor:
    """
    Intercepts Cohere API calls.
    
    Records and replays requests to Cohere's text generation,
    embeddings, and other models.
    """
    
    def __init__(self, storage: "Storage", analytics: "Analytics") -> None:
        """
        Initialize the Cohere interceptor.
        
        Args:
            storage: Storage backend
            analytics: Analytics tracker
        """
        self.storage = storage
        self.analytics = analytics
        self.original_methods: Dict[str, Any] = {}
    
    def activate(self) -> None:
        """Patch Cohere methods."""
        try:
            import cohere
            
            # Store originals
            self.original_methods['generate'] = cohere.Client.generate
            self.original_methods['embed'] = cohere.Client.embed
            
            # Patch generate
            @functools.wraps(cohere.Client.generate)
            def wrapped_generate(client_self, *args, **kwargs):
                call_hash = self.storage.create_hash(args, kwargs, "cohere_v1")
                session_id = kwargs.pop('session_id', 'default_cohere_session')
                
                cached = self.storage.load(session_id, call_hash)
                if cached:
                    logger.info("✈️  [REPLAY] Using cached Cohere response")
                    self.analytics.record_replay(session_id, call_hash)
                    return cached['output']
                
                logger.info("🔴 [RECORD] Calling Cohere API...")
                result = self.original_methods['generate'](client_self, *args, **kwargs)
                
                self.storage.save(
                    session_id=session_id,
                    call_hash=call_hash,
                    data={
                        "provider": "cohere",
                        "input": {"args": args, "kwargs": kwargs},
                        "output": result
                    },
                    cost=0
                )
                
                self.analytics.record_live_call(session_id, call_hash, cost=0)
                return result
            
            # Patch embed
            @functools.wraps(cohere.Client.embed)
            def wrapped_embed(client_self, *args, **kwargs):
                call_hash = self.storage.create_hash(args, kwargs, "cohere_embed_v1")
                session_id = kwargs.pop('session_id', 'default_cohere_session')
                
                cached = self.storage.load(session_id, call_hash)
                if cached:
                    logger.info("✈️  [REPLAY] Using cached Cohere embeddings")
                    self.analytics.record_replay(session_id, call_hash)
                    return cached['output']
                
                logger.info("🔴 [RECORD] Calling Cohere Embed...")
                result = self.original_methods['embed'](client_self, *args, **kwargs)
                
                self.storage.save(
                    session_id=session_id,
                    call_hash=call_hash,
                    data={
                        "provider": "cohere_embed",
                        "input": {"args": args, "kwargs": kwargs},
                        "output": result
                    },
                    cost=0
                )
                
                self.analytics.record_live_call(session_id, call_hash, cost=0)
                return result
            
            cohere.Client.generate = wrapped_generate
            cohere.Client.embed = wrapped_embed
            logger.info("✅ Cohere interceptor activated")
        
        except ImportError:
            logger.warning("⚠️  cohere not installed, skipping interceptor")
    
    def deactivate(self) -> None:
        """Restore original Cohere methods."""
        try:
            import cohere
            if 'generate' in self.original_methods:
                cohere.Client.generate = self.original_methods['generate']
            if 'embed' in self.original_methods:
                cohere.Client.embed = self.original_methods['embed']
            logger.info("✅ Cohere interceptor deactivated")
        except ImportError:
            pass


class HuggingFaceInterceptor:
    """
    Intercepts HuggingFace Inference API calls.
    
    Records and replays requests to HuggingFace's inference endpoints.
    """
    
    def __init__(self, storage: "Storage", analytics: "Analytics") -> None:
        """
        Initialize the HuggingFace interceptor.
        
        Args:
            storage: Storage backend
            analytics: Analytics tracker
        """
        self.storage = storage
        self.analytics = analytics
        self.original_methods: Dict[str, Any] = {}
    
    def activate(self) -> None:
        """Patch HuggingFace methods."""
        try:
            from huggingface_hub import InferenceClient
            
            # Store original
            self.original_methods['text_generation'] = InferenceClient.text_generation
            
            @functools.wraps(InferenceClient.text_generation)
            def wrapped_text_generation(client_self, *args, **kwargs):
                call_hash = self.storage.create_hash(args, kwargs, "huggingface_v1")
                session_id = kwargs.pop('session_id', 'default_hf_session')
                
                cached = self.storage.load(session_id, call_hash)
                if cached:
                    logger.info("✈️  [REPLAY] Using cached HuggingFace response")
                    self.analytics.record_replay(session_id, call_hash)
                    return cached['output']
                
                logger.info("🔴 [RECORD] Calling HuggingFace API...")
                result = self.original_methods['text_generation'](client_self, *args, **kwargs)
                
                self.storage.save(
                    session_id=session_id,
                    call_hash=call_hash,
                    data={
                        "provider": "huggingface",
                        "input": {"args": args, "kwargs": kwargs},
                        "output": result
                    },
                    cost=0
                )
                
                self.analytics.record_live_call(session_id, call_hash, cost=0)
                return result
            
            InferenceClient.text_generation = wrapped_text_generation
            logger.info("✅ HuggingFace interceptor activated")
        
        except ImportError:
            logger.warning("⚠️  huggingface-hub not installed, skipping interceptor")
    
    def deactivate(self) -> None:
        """Restore original HuggingFace methods."""
        try:
            from huggingface_hub import InferenceClient
            if 'text_generation' in self.original_methods:
                InferenceClient.text_generation = self.original_methods['text_generation']
                logger.info("✅ HuggingFace interceptor deactivated")
        except ImportError:
            pass
