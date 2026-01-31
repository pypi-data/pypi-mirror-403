"""
HLA-Compass Python SDK

SDK for developing modules on the HLA-Compass platform.
"""

from ._version import __version__

# Core module base class
from .module import Module, ModuleError, ValidationError

# Data access classes
from .data import DataClient, DataAccessError

# Authentication
from .auth import Auth, AuthError

# Storage utilities
from .storage import Storage, StorageError

# Runtime context
from .context import RuntimeContext, ContextValidationError, CreditReservation, WorkflowMetadata

# CLI utilities
from .cli import main as cli_main

# Types
from .types import (
    ExecutionContext,
    ModuleInput,
    ModuleOutput,
    JobStatus,
    ComputeType,
    ModuleType,
)


__all__ = [
    # Version
    "__version__",
    # Core classes
    "Module",
    "ModuleError",
    "ValidationError",
    # Data access
    "DataClient",
    "DataAccessError",
    # Auth
    "Auth",
    "AuthError",
    # Storage
    "Storage",
    "StorageError",
    # Context
    "RuntimeContext",
    "ContextValidationError",
    "CreditReservation",
    "WorkflowMetadata",
    # CLI
    "cli_main",
    # Types
    "ExecutionContext",
    "ModuleInput",
    "ModuleOutput",
    "JobStatus",
    "ComputeType",
    "ModuleType",
]
