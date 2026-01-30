"""
MOSS LangGraph Integration - Explicit Signing Functions

Explicit signing functions for LangGraph node outputs and checkpoints.
"""

from typing import Any, Dict, Optional

from moss import sign, sign_async, verify, SignResult, VerifyResult


def _extract_state_payload(state: Any) -> Dict[str, Any]:
    """Extract payload from LangGraph state."""
    if isinstance(state, dict):
        # Exclude moss_envelope if present
        return {k: v for k, v in state.items() if k != "moss_envelope"}
    
    if hasattr(state, "dict"):
        d = state.dict()
        d.pop("moss_envelope", None)
        return d
    
    if hasattr(state, "__dict__"):
        d = {k: v for k, v in state.__dict__.items() if not k.startswith("_") and k != "moss_envelope"}
        return d
    
    return {"state": str(state)}


def _extract_checkpoint_payload(checkpoint: Any) -> Dict[str, Any]:
    """Extract payload from LangGraph checkpoint."""
    if isinstance(checkpoint, dict):
        return {"type": "checkpoint", **checkpoint}
    
    if hasattr(checkpoint, "to_dict"):
        return {"type": "checkpoint", **checkpoint.to_dict()}
    
    return {"type": "checkpoint", "data": str(checkpoint)}


def sign_node_output(
    output: Any,
    agent_id: str,
    *,
    node: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a LangGraph node output.
    
    Args:
        output: Node output (typically state dict)
        agent_id: Identifier for the agent/graph
        node: Name of the node that produced this output
        context: Optional context (user_id, session_id, etc.)
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        def my_node(state):
            result = process(state)
            signed = sign_node_output(result, agent_id="my-graph", node="processor")
            return result
    """
    payload = _extract_state_payload(output)
    if node:
        payload["_node"] = node
    
    action = f"node:{node}" if node else "node_output"
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


async def sign_node_output_async(
    output: Any,
    agent_id: str,
    *,
    node: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_node_output."""
    payload = _extract_state_payload(output)
    if node:
        payload["_node"] = node
    
    action = f"node:{node}" if node else "node_output"
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


def sign_checkpoint(
    checkpoint: Any,
    agent_id: str,
    *,
    checkpoint_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a LangGraph checkpoint.
    
    Args:
        checkpoint: Checkpoint data
        agent_id: Identifier for the agent/graph
        checkpoint_id: Optional checkpoint identifier
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = _extract_checkpoint_payload(checkpoint)
    if checkpoint_id:
        payload["checkpoint_id"] = checkpoint_id
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action="checkpoint",
        context=context,
    )


async def sign_checkpoint_async(
    checkpoint: Any,
    agent_id: str,
    *,
    checkpoint_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_checkpoint."""
    payload = _extract_checkpoint_payload(checkpoint)
    if checkpoint_id:
        payload["checkpoint_id"] = checkpoint_id
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="checkpoint",
        context=context,
    )


def sign_state_transition(
    from_state: Any,
    to_state: Any,
    agent_id: str,
    *,
    from_node: Optional[str] = None,
    to_node: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a state transition between nodes.
    
    Args:
        from_state: State before transition
        to_state: State after transition
        agent_id: Identifier for the agent/graph
        from_node: Source node name
        to_node: Target node name
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = {
        "type": "state_transition",
        "from_state": _extract_state_payload(from_state),
        "to_state": _extract_state_payload(to_state),
    }
    
    if from_node:
        payload["from_node"] = from_node
    if to_node:
        payload["to_node"] = to_node
    
    transition = f"{from_node or 'start'}->{to_node or 'end'}"
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=f"transition:{transition}",
        context=context,
    )


async def sign_state_transition_async(
    from_state: Any,
    to_state: Any,
    agent_id: str,
    *,
    from_node: Optional[str] = None,
    to_node: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_state_transition."""
    payload = {
        "type": "state_transition",
        "from_state": _extract_state_payload(from_state),
        "to_state": _extract_state_payload(to_state),
    }
    
    if from_node:
        payload["from_node"] = from_node
    if to_node:
        payload["to_node"] = to_node
    
    transition = f"{from_node or 'start'}->{to_node or 'end'}"
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=f"transition:{transition}",
        context=context,
    )


def verify_envelope(envelope: Any, payload: Any = None) -> VerifyResult:
    """
    Verify a signed envelope.
    
    Args:
        envelope: MOSS Envelope or dict
        payload: Original payload for hash verification (optional)
    
    Returns:
        VerifyResult with valid=True/False and details
    """
    return verify(envelope, payload)
