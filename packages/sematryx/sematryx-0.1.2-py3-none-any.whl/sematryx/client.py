"""
Sematryx SDK Client
"""

import inspect
import os
import textwrap
from typing import Any, Callable, Dict, List, Optional, Union
import httpx

from .models import (
    OptimizationRequest,
    OptimizationResult,
    Variable,
    Constraint,
    LearningConfig,
    UsageInfo,
    HealthStatus,
)
from .exceptions import (
    SematryxError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    OptimizationError,
    ConnectionError,
)


# Default to Kubernetes deployment endpoint
# Production Kubernetes endpoint: http://34.173.137.195/v1
# Set SEMATRYX_API_URL environment variable to override
# To get your Kubernetes IP: kubectl get service sematryx-api-service -n sematryx -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
DEFAULT_BASE_URL = os.getenv(
    "SEMATRYX_API_URL",
    "http://34.173.137.195/v1"  # Production Kubernetes LoadBalancer IP
)
DEFAULT_TIMEOUT = 300.0  # 5 minutes for optimization


def _extract_function_source(func: Callable, variable_names: List[str]) -> str:
    """
    Extract and convert a Python function to a string expression.
    
    Handles simple functions that can be converted to expressions.
    For complex functions, raises an error suggesting webhook mode.
    """
    try:
        source = inspect.getsource(func)
        source = textwrap.dedent(source)
        
        # Parse the function to extract the return expression
        lines = source.strip().split('\n')
        
        # Find return statement
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('return '):
                expr = stripped[7:].strip()
                
                # Get function signature to map parameter names
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                
                # If function takes a single array parameter (e.g., def f(x):)
                if len(params) == 1:
                    param_name = params[0]
                    # Replace array indexing with variable names
                    # e.g., x[0] -> first_var_name, x[1] -> second_var_name
                    for i, var_name in enumerate(variable_names):
                        expr = expr.replace(f'{param_name}[{i}]', var_name)
                    # Also handle iteration patterns like "xi" in comprehensions
                    # Keep as-is since the API understands x[i] notation
                
                # If function takes multiple parameters matching variable names
                elif len(params) == len(variable_names):
                    # Map function params to variable names if different
                    for old_name, new_name in zip(params, variable_names):
                        if old_name != new_name:
                            # Simple replacement (may need more sophisticated parsing for complex cases)
                            expr = expr.replace(old_name, new_name)
                
                return expr
        
        raise ValueError("Could not find return statement in function")
        
    except (OSError, TypeError) as e:
        # Can't get source (e.g., built-in function, lambda defined inline)
        raise SematryxError(
            f"Cannot extract source from function. For complex functions, use webhook mode:\n"
            f"  client.optimize(objective_url='https://your-api.com/evaluate', ...)\n"
            f"Original error: {e}"
        )


def _is_simple_function(func: Callable) -> bool:
    """Check if a function is simple enough to convert to a string expression."""
    try:
        source = inspect.getsource(func)
        # Simple heuristics: single return statement, no imports, no complex control flow
        lines = [l.strip() for l in source.split('\n') if l.strip() and not l.strip().startswith('#')]
        
        # Remove docstrings
        in_docstring = False
        filtered_lines = []
        for line in lines:
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
                continue
            if not in_docstring:
                filtered_lines.append(line)
        
        # Should be just def + return (maybe with simple assignments)
        has_def = any(l.startswith('def ') for l in filtered_lines)
        has_return = any(l.startswith('return ') for l in filtered_lines)
        has_complex = any(
            l.startswith(('if ', 'for ', 'while ', 'try:', 'import ', 'from '))
            for l in filtered_lines
        )
        
        return has_def and has_return and not has_complex
        
    except (OSError, TypeError):
        return False


class Sematryx:
    """
    Sematryx Python SDK Client
    
    Example:
        client = Sematryx(api_key="sk-...")
        
        # Option 1: Pass a Python function directly
        def my_objective(x):
            return x[0]**2 + x[1]**2
        
        result = client.optimize(
            objective="minimize",
            variables=[
                {"name": "x", "bounds": (-5, 5)},
                {"name": "y", "bounds": (-5, 5)},
            ],
            objective_function=my_objective,
        )
        
        # Option 2: String expression (simple cases)
        result = client.optimize(
            variables=[{"name": "x", "bounds": (-5, 5)}],
            objective_function="x**2",
        )
        
        # Option 3: Webhook for complex/production use
        result = client.optimize(
            variables=[{"name": "x", "bounds": (-5, 5)}],
            objective_url="https://my-api.com/evaluate",
        )
        
        print(result.solution)  # {'x': 0.0, 'y': 0.0}
        print(result.explanation)  # "Converged to global minimum..."
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize Sematryx Client.
        
        Args:
            api_key: Your Sematryx API key (starts with 'sematryx_', 'sk-', or 'sematryx_')
            base_url: API base URL (default: from SEMATRYX_API_URL env var or Kubernetes endpoint)
            timeout: Request timeout in seconds (default: 300)
        """
        # base_url will have a default from DEFAULT_BASE_URL, so this check is no longer needed
        # But we keep it for clarity if someone explicitly passes empty string
        if not base_url:
            raise ValueError(
                "base_url cannot be empty. Set SEMATRYX_API_URL environment variable or pass base_url parameter. "
                "Example: export SEMATRYX_API_URL='http://<KUBERNETES_IP>/v1'"
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "sematryx-python/0.1.0",
            },
            timeout=timeout,
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def close(self):
        """Close the HTTP client"""
        self._client.close()
    
    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and raise appropriate exceptions"""
        if response.status_code == 200:
            return response.json()
        
        try:
            error_data = response.json()
            message = error_data.get("detail", error_data.get("message", "Unknown error"))
        except Exception:
            message = response.text or "Unknown error"
        
        if response.status_code == 401:
            raise AuthenticationError(message, status_code=401)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message, 
                status_code=429, 
                retry_after=int(retry_after) if retry_after else None
            )
        elif response.status_code == 422:
            errors = error_data.get("errors", []) if isinstance(error_data, dict) else []
            raise ValidationError(message, status_code=422, errors=errors)
        elif response.status_code >= 500:
            raise SematryxError(f"Server error: {message}", status_code=response.status_code)
        else:
            raise SematryxError(message, status_code=response.status_code)
    
    def optimize(
        self,
        objective: str = "minimize",
        variables: List[Union[Variable, Dict[str, Any]]] = None,
        objective_function: Optional[Union[str, Callable]] = None,
        objective_url: Optional[str] = None,
        constraints: List[Union[Constraint, Dict[str, Any]]] = None,
        max_evaluations: int = 1000,
        strategy: str = "auto",
        explanation_level: int = 2,
        learning: Optional[Union[LearningConfig, Dict[str, Any]]] = None,
        domain: Optional[str] = None,
        **kwargs,
    ) -> OptimizationResult:
        """
        Run an optimization.
        
        Args:
            objective: "minimize" or "maximize"
            variables: List of variable definitions with names and bounds
            objective_function: Objective as a Python function OR string expression
            objective_url: Webhook URL for complex objectives (API calls your endpoint)
            constraints: List of constraint definitions
            max_evaluations: Maximum function evaluations
            strategy: Optimization strategy ("auto", "bayesian", "evolutionary", "gradient")
            explanation_level: 0-4, higher = more detailed explanations
            learning: Private Learning Store configuration
            domain: Domain hint (financial, healthcare, supply_chain, etc.)
            **kwargs: Additional parameters
            
        Returns:
            OptimizationResult with solution, explanation, and audit trail
            
        Examples:
            # Python function (simple cases - auto-converted to expression)
            def sphere(x):
                return x[0]**2 + x[1]**2
            
            result = client.optimize(
                variables=[{"name": "a", "bounds": (-5, 5)}, {"name": "b", "bounds": (-5, 5)}],
                objective_function=sphere,
            )
            
            # String expression
            result = client.optimize(
                variables=[{"name": "x", "bounds": (-5, 5)}],
                objective_function="x**2 + 2*x + 1",
            )
            
            # Webhook (for complex real-world problems)
            result = client.optimize(
                variables=[{"name": "x", "bounds": (0, 100)}],
                objective_url="https://my-api.com/evaluate",
            )
        """
        # Convert dicts to models
        if variables:
            variables = [
                Variable(**v) if isinstance(v, dict) else v 
                for v in variables
            ]
        
        variable_names = [v.name if isinstance(v, Variable) else v["name"] for v in (variables or [])]
        
        # Handle objective_function: can be string, callable, or None (if using webhook)
        objective_function_str = None
        
        if objective_url:
            # Webhook mode - objective_function not needed
            if objective_function:
                raise ValueError("Cannot specify both objective_function and objective_url")
        elif callable(objective_function):
            # Python function - try to extract source
            if _is_simple_function(objective_function):
                objective_function_str = _extract_function_source(objective_function, variable_names)
            else:
                raise SematryxError(
                    "Complex functions cannot be sent to the API. Options:\n"
                    "1. Use a simple expression: objective_function='x**2 + y**2'\n"
                    "2. Use webhook mode: objective_url='https://your-api.com/evaluate'\n"
                    "   Your endpoint receives POST with {'variables': {'x': 1.5, 'y': 2.0}}\n"
                    "   and should return {'value': 6.25}"
                )
        elif isinstance(objective_function, str):
            objective_function_str = objective_function
        elif objective_function is None and not objective_url:
            raise ValueError("Must provide either objective_function or objective_url")
        
        if constraints:
            constraints = [
                Constraint(**c) if isinstance(c, dict) else c
                for c in constraints
            ]
        
        if learning and isinstance(learning, dict):
            learning = LearningConfig(**learning)
        
        # Extract tetrad_config from kwargs if provided
        tetrad_config = kwargs.pop('tetrad_config', None)
        
        # Build request payload
        request_data = {
            "objective": objective,
            "variables": [v.model_dump() if isinstance(v, Variable) else v for v in (variables or [])],
            "constraints": [c.model_dump() if isinstance(c, Constraint) else c for c in (constraints or [])],
            "max_evaluations": max_evaluations,
            "strategy": strategy,
            "explanation_level": explanation_level,
            "domain": domain,
            "metadata": kwargs,
        }
        
        if objective_function_str:
            request_data["objective_function"] = objective_function_str
        if objective_url:
            request_data["objective_url"] = objective_url
        if learning:
            request_data["learning"] = learning.model_dump() if isinstance(learning, LearningConfig) else learning
        if tetrad_config:
            request_data["tetrad_config"] = tetrad_config
        
        try:
            response = self._client.post(
                "/optimize",
                json={k: v for k, v in request_data.items() if v is not None},
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to Sematryx API: {e}")
        except httpx.TimeoutException:
            raise SematryxError("Request timed out. Try increasing the timeout or reducing max_evaluations.")
        
        data = self._handle_response(response)
        
        return OptimizationResult(
            success=data.get("success", True),
            solution=data.get("solution", {}),
            objective_value=data.get("objective_value", 0.0),
            constraints_satisfied=data.get("constraints_satisfied", True),
            evaluations_used=data.get("evaluations_used", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            strategy_used=data.get("strategy_used", "unknown"),
            explanation=data.get("explanation"),
            explanation_detail=data.get("explanation_detail"),
            audit_id=data.get("audit_id"),
            learning_operations=data.get("learning_operations"),
            stored_to_public=data.get("stored_to_public", False),
            stored_to_private=data.get("stored_to_private", False),
            public_recall_count=data.get("public_recall_count", 0) or 0,
            private_recall_count=data.get("private_recall_count", 0) or 0,
            raw_response=data,
        )
    
    def get_usage(self) -> UsageInfo:
        """Get current usage information for your account"""
        response = self._client.get("/usage")
        data = self._handle_response(response)
        return UsageInfo(**data)
    
    def health(self) -> HealthStatus:
        """Check API health status"""
        response = self._client.get("/health")
        data = self._handle_response(response)
        return HealthStatus(**data)
    
    # Convenience methods for common domains
    
    def optimize_portfolio(
        self,
        assets: List[str],
        returns: List[float],
        covariance: List[List[float]],
        target_return: Optional[float] = None,
        max_position: float = 1.0,
        **kwargs,
    ) -> OptimizationResult:
        """
        Portfolio optimization with financial constraints.
        
        Args:
            assets: List of asset names
            returns: Expected returns for each asset
            covariance: Covariance matrix
            target_return: Minimum target return (optional)
            max_position: Maximum weight per asset
            **kwargs: Additional optimization parameters
        """
        return self.optimize(
            domain="financial",
            variables=[
                {"name": asset, "bounds": (0, max_position)} 
                for asset in assets
            ],
            constraints=[
                {"expression": f"sum([{', '.join(assets)}]) == 1", "type": "equality"},
            ] + ([
                {"expression": f"sum([r * w for r, w in zip({returns}, [{', '.join(assets)}])]) >= {target_return}", "type": "inequality"}
            ] if target_return else []),
            metadata={
                "problem_type": "portfolio",
                "returns": returns,
                "covariance": covariance,
            },
            **kwargs,
        )
    
    def optimize_supply_chain(
        self,
        nodes: List[str],
        demands: Dict[str, float],
        capacities: Dict[str, float],
        costs: Dict[str, Dict[str, float]],
        **kwargs,
    ) -> OptimizationResult:
        """
        Supply chain routing optimization.
        
        Args:
            nodes: List of node names (warehouses, customers, etc.)
            demands: Demand at each node
            capacities: Capacity at each node  
            costs: Cost matrix between nodes
            **kwargs: Additional optimization parameters
        """
        return self.optimize(
            domain="supply_chain",
            metadata={
                "problem_type": "routing",
                "nodes": nodes,
                "demands": demands,
                "capacities": capacities,
                "costs": costs,
            },
            **kwargs,
        )


class AsyncSematryx:
    """
    Async Sematryx Python SDK Client
    
    Example:
        async with AsyncSematryx(api_key="sk-...") as client:
            result = await client.optimize(
                objective="minimize",
                variables=[{"name": "x", "bounds": (-5, 5)}],
                objective_function="x**2",
            )
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "sematryx-python/0.1.0",
            },
            timeout=timeout,
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    async def close(self):
        await self._client.aclose()
    
    async def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response and raise appropriate exceptions"""
        if response.status_code == 200:
            return response.json()
        
        try:
            error_data = response.json()
            message = error_data.get("detail", error_data.get("message", "Unknown error"))
        except Exception:
            message = response.text or "Unknown error"
        
        if response.status_code == 401:
            raise AuthenticationError(message, status_code=401)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                status_code=429,
                retry_after=int(retry_after) if retry_after else None
            )
        elif response.status_code == 422:
            errors = error_data.get("errors", []) if isinstance(error_data, dict) else []
            raise ValidationError(message, status_code=422, errors=errors)
        elif response.status_code >= 500:
            raise SematryxError(f"Server error: {message}", status_code=response.status_code)
        else:
            raise SematryxError(message, status_code=response.status_code)
    
    async def optimize(
        self,
        objective: str = "minimize",
        variables: List[Union[Variable, Dict[str, Any]]] = None,
        objective_function: Optional[Union[str, Callable]] = None,
        objective_url: Optional[str] = None,
        constraints: List[Union[Constraint, Dict[str, Any]]] = None,
        max_evaluations: int = 1000,
        strategy: str = "auto",
        explanation_level: int = 2,
        learning: Optional[Union[LearningConfig, Dict[str, Any]]] = None,
        domain: Optional[str] = None,
        **kwargs,
    ) -> OptimizationResult:
        """Async version of optimize. See Sematryx.optimize for documentation."""
        # Convert dicts to models
        if variables:
            variables = [
                Variable(**v) if isinstance(v, dict) else v
                for v in variables
            ]
        
        variable_names = [v.name if isinstance(v, Variable) else v["name"] for v in (variables or [])]
        
        # Handle objective_function
        objective_function_str = None
        
        if objective_url:
            if objective_function:
                raise ValueError("Cannot specify both objective_function and objective_url")
        elif callable(objective_function):
            if _is_simple_function(objective_function):
                objective_function_str = _extract_function_source(objective_function, variable_names)
            else:
                raise SematryxError(
                    "Complex functions cannot be sent to the API. Use webhook mode:\n"
                    "  objective_url='https://your-api.com/evaluate'"
                )
        elif isinstance(objective_function, str):
            objective_function_str = objective_function
        elif objective_function is None and not objective_url:
            raise ValueError("Must provide either objective_function or objective_url")
        
        if constraints:
            constraints = [
                Constraint(**c) if isinstance(c, dict) else c
                for c in constraints
            ]
        
        if learning and isinstance(learning, dict):
            learning = LearningConfig(**learning)
        
        request_data = {
            "objective": objective,
            "variables": [v.model_dump() if isinstance(v, Variable) else v for v in (variables or [])],
            "constraints": [c.model_dump() if isinstance(c, Constraint) else c for c in (constraints or [])],
            "max_evaluations": max_evaluations,
            "strategy": strategy,
            "explanation_level": explanation_level,
            "domain": domain,
            "metadata": kwargs,
        }
        
        if objective_function_str:
            request_data["objective_function"] = objective_function_str
        if objective_url:
            request_data["objective_url"] = objective_url
        if learning:
            request_data["learning"] = learning.model_dump() if isinstance(learning, LearningConfig) else learning
        
        try:
            response = await self._client.post(
                "/optimize",
                json={k: v for k, v in request_data.items() if v is not None},
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to Sematryx API: {e}")
        except httpx.TimeoutException:
            raise SematryxError("Request timed out. Try increasing the timeout or reducing max_evaluations.")
        
        data = self._handle_response(response)
        
        return OptimizationResult(
            success=data.get("success", True),
            solution=data.get("solution", {}),
            objective_value=data.get("objective_value", 0.0),
            constraints_satisfied=data.get("constraints_satisfied", True),
            evaluations_used=data.get("evaluations_used", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            strategy_used=data.get("strategy_used", "unknown"),
            explanation=data.get("explanation"),
            explanation_detail=data.get("explanation_detail"),
            audit_id=data.get("audit_id"),
            learning_operations=data.get("learning_operations"),
            stored_to_public=data.get("stored_to_public", False),
            stored_to_private=data.get("stored_to_private", False),
            public_recall_count=data.get("public_recall_count", 0) or 0,
            private_recall_count=data.get("private_recall_count", 0) or 0,
            raw_response=data,
        )
    
    async def get_usage(self) -> UsageInfo:
        response = await self._client.get("/usage")
        data = self._handle_response(response)
        return UsageInfo(**data)
    
    async def health(self) -> HealthStatus:
        response = await self._client.get("/health")
        data = self._handle_response(response)
        return HealthStatus(**data)
