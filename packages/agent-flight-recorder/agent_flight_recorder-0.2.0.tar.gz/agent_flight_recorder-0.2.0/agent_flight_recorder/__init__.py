
"""
Agent Flight Recorder - Debug AI Agents without burning money.

Record and replay expensive API calls to save costs during development and testing.
"""

__version__ = "0.1.0"

from .recorder import Recorder
from .analytics import Analytics
from .streaming import StreamRecorder
from .filtering import DataFilter
from .providers import GoogleVertexAIInterceptor, CohereInterceptor, HuggingFaceInterceptor

__all__ = [
    "Recorder",
    "Analytics",
    "StreamRecorder",
    "DataFilter",
    "GoogleVertexAIInterceptor",
    "CohereInterceptor",
    "HuggingFaceInterceptor"
]