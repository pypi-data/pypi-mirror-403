"""Artifact caching and registry integration.

This module provides:

- Local wheel caching with LRU eviction
- Content-addressable storage using wheel hashes
- Registry integration for private wheel hosting
- Cache statistics and management
"""

from __future__ import annotations

from headless_wheel_builder.cache.models import (
    CacheEntry,
    CacheStats,
    RegistryConfig,
)
from headless_wheel_builder.cache.storage import ArtifactCache
from headless_wheel_builder.cache.registry import WheelRegistry

__all__ = [
    "ArtifactCache",
    "CacheEntry",
    "CacheStats",
    "RegistryConfig",
    "WheelRegistry",
]
