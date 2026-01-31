"""
Phylax - Deterministic regression enforcement for LLM systems.

Public API:
    trace       - Decorator to trace LLM calls
    expect      - Decorator to add expectations
    execution   - Context manager for grouping traces
    Trace       - Trace data model
    Verdict     - Verdict enum (PASS, FAIL, TAINTED)
"""

from phylax._internal.schema import (
    Trace,
    TraceRequest,
    TraceResponse,
    TraceRuntime,
    Verdict,
)
from phylax._internal.decorator import trace, expect
from phylax._internal.context import execution
from phylax._internal.graph import ExecutionGraph, NodeRole, GraphStage, GraphDiff, NodeDiff

__version__ = "1.0.2"
__all__ = [
    # Core decorators
    "trace",
    "expect",
    # Context manager
    "execution",
    # Data models
    "Trace",
    "TraceRequest",
    "TraceResponse",
    "TraceRuntime",
    "Verdict",
    # Graph (advanced)
    "ExecutionGraph",
    "NodeRole",
    "GraphStage",
    "GraphDiff",
    "NodeDiff",
    # Version
    "__version__",
]
