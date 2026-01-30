"""
MOSS LangGraph Integration - Cryptographic Signing for LangGraph

Sign node outputs, checkpoints, and state transitions explicitly.

Quick Start:
    from langgraph.graph import StateGraph
    from moss_langgraph import sign_node_output
    
    def my_node(state):
        result = process(state)
        signed = sign_node_output(result, agent_id="my-graph", node="processor")
        return result

Enterprise Mode:
    Set MOSS_API_KEY for policy evaluation and evidence retention.
"""

__version__ = "0.2.0"

# Explicit signing (recommended)
from .signing import (
    sign_node_output,
    sign_node_output_async,
    sign_checkpoint,
    sign_checkpoint_async,
    sign_state_transition,
    sign_state_transition_async,
    verify_envelope,
)

# Core types
from moss import SignResult, VerifyResult, Envelope, enterprise_enabled

# Legacy (backwards compatibility)
from .wrapper import signed_node, SignedNodeFactory

__all__ = [
    # Explicit signing
    "sign_node_output",
    "sign_node_output_async",
    "sign_checkpoint",
    "sign_checkpoint_async",
    "sign_state_transition",
    "sign_state_transition_async",
    "verify_envelope",
    
    # Core types
    "SignResult",
    "VerifyResult",
    "Envelope",
    "enterprise_enabled",
    
    # Legacy
    "signed_node",
    "SignedNodeFactory",
]
