"""File tracking and override detection for Prism.

This module provides file tracking, manifest management, and override logging
to enable safe regeneration of code.
"""

from prism.tracking.differ import (
    DiffGenerator,
    DiffSummary,
)
from prism.tracking.logger import (
    Override,
    OverrideLog,
    OverrideLogger,
)
from prism.tracking.manifest import (
    FileManifest,
    ManifestManager,
    TrackedFile,
)

__all__ = [
    "DiffGenerator",
    "DiffSummary",
    "FileManifest",
    "ManifestManager",
    "Override",
    "OverrideLog",
    "OverrideLogger",
    "TrackedFile",
]
