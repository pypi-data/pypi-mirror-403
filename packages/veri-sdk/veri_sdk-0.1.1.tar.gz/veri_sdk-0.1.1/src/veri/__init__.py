"""
Veri SDK - Python client for Veri Deepfake Detection API
"""

from veri.client import AsyncVeriClient, VeriClient
from veri.errors import (
    VeriAPIError,
    VeriError,
    VeriInsufficientCreditsError,
    VeriRateLimitError,
    VeriTimeoutError,
    VeriValidationError,
)
from veri.types import (
    DetectionOptions,
    DetectionResult,
    ModelResult,
)

__version__ = "0.1.1"
__all__ = [
    # Clients
    "VeriClient",
    "AsyncVeriClient",
    # Types
    "DetectionResult",
    "DetectionOptions",
    "ModelResult",
    # Errors
    "VeriError",
    "VeriAPIError",
    "VeriValidationError",
    "VeriTimeoutError",
    "VeriRateLimitError",
    "VeriInsufficientCreditsError",
]
