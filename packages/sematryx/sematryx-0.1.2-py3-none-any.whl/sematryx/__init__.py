"""
Sematryx Python SDK
===================

AI-powered optimization that explains itself.

Quick Start:
    from sematryx import Sematryx
    
    client = Sematryx(api_key="your-api-key")
    
    result = client.optimize(
        objective="minimize",
        variables=[
            {"name": "x", "bounds": [-5, 5]},
            {"name": "y", "bounds": [-5, 5]},
        ],
        objective_function="x**2 + y**2",
    )
    
    print(f"Solution: {result.solution}")
    print(f"Explanation: {result.explanation}")

For more examples, see https://sematryx.com/docs
"""

__version__ = "0.1.2"

from .client import Sematryx, AsyncSematryx
from .models import (
    OptimizationRequest,
    OptimizationResult,
    Variable,
    Constraint,
    LearningConfig,
)
from .exceptions import (
    SematryxError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    OptimizationError,
)

__all__ = [
    # Main clients
    "Sematryx",
    "AsyncSematryx",
    # Models
    "OptimizationRequest",
    "OptimizationResult",
    "Variable",
    "Constraint",
    "LearningConfig",
    # Exceptions
    "SematryxError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "OptimizationError",
    # Version
    "__version__",
]

