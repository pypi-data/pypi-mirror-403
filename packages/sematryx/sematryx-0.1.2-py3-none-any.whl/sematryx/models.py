"""
Sematryx SDK Data Models
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class Variable(BaseModel):
    """Optimization variable definition"""
    name: str
    bounds: tuple[float, float]
    type: str = "continuous"  # continuous, integer, binary
    initial_value: Optional[float] = None


class Constraint(BaseModel):
    """Optimization constraint definition"""
    expression: str
    type: str = "inequality"  # inequality, equality
    description: Optional[str] = None


class LearningConfig(BaseModel):
    """Private Learning Store configuration"""
    read_from_public: bool = True
    read_from_private: bool = True
    write_to_public: bool = False
    write_to_private: bool = True


class OptimizationRequest(BaseModel):
    """Request payload for optimization"""
    objective: str = "minimize"  # minimize or maximize
    variables: List[Variable]
    objective_function: Optional[str] = None
    constraints: List[Constraint] = Field(default_factory=list)
    max_evaluations: int = 1000
    strategy: str = "auto"  # auto, bayesian, evolutionary, gradient
    explanation_level: int = 2  # 0-4
    learning: Optional[LearningConfig] = None
    domain: Optional[str] = None  # financial, healthcare, supply_chain, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExplanationDetail(BaseModel):
    """Detailed explanation of optimization decision"""
    rationale: str
    alternatives_considered: int
    strategy_selected: str
    convergence_reason: str
    confidence_score: float


class OptimizationResult(BaseModel):
    """Result from optimization"""
    success: bool
    solution: Dict[str, float]
    objective_value: float
    constraints_satisfied: bool
    evaluations_used: int
    duration_seconds: float
    strategy_used: str
    
    # Explanation (if requested)
    explanation: Optional[str] = None
    explanation_detail: Optional[ExplanationDetail] = None
    
    # Audit trail
    audit_id: Optional[str] = None
    
    # Learning store operations
    learning_operations: Optional[Dict[str, Any]] = None
    stored_to_public: bool = False
    stored_to_private: bool = False
    public_recall_count: int = 0
    private_recall_count: int = 0

    # Raw response for advanced use
    raw_response: Optional[Dict[str, Any]] = None


class UsageInfo(BaseModel):
    """Account usage information"""
    tier: str
    optimizations_used: int
    optimizations_limit: int
    private_storage_used_mb: float
    private_storage_limit_mb: float
    learning_accesses_used: int
    learning_accesses_limit: int


class HealthStatus(BaseModel):
    """API health status"""
    status: str
    version: str
    latency_ms: float

