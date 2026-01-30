"""Tests for moss-langgraph signing functions."""

import pytest
from unittest.mock import MagicMock

from moss_langgraph import (
    sign_node_output,
    sign_checkpoint,
    sign_state_transition,
    verify_envelope,
    SignResult,
)


class TestSignNodeOutput:
    """Test sign_node_output function."""
    
    def test_sign_node_output_dict(self):
        """Sign a node output from dict state."""
        state = {
            "input": "Hello",
            "output": "World",
        }
        
        result = sign_node_output(state, agent_id="test-graph")
        
        assert isinstance(result, SignResult)
        assert result.payload["input"] == "Hello"
        assert result.payload["output"] == "World"
    
    def test_sign_node_output_with_node_name(self):
        """Sign node output with node name."""
        state = {"result": "processed"}
        
        result = sign_node_output(
            state,
            agent_id="test-graph",
            node="processor",
        )
        
        assert result.payload.get("_node") == "processor"
    
    def test_sign_node_output_excludes_moss_envelope(self):
        """State signing excludes existing moss_envelope."""
        state = {
            "data": "test",
            "moss_envelope": {"existing": "envelope"},
        }
        
        result = sign_node_output(state, agent_id="test-graph")
        
        assert "moss_envelope" not in result.payload
        assert result.payload["data"] == "test"
    
    def test_sign_node_output_with_context(self):
        """Sign node output with context."""
        state = {"action": "transfer"}
        
        result = sign_node_output(
            state,
            agent_id="finance-graph",
            context={"user_id": "u123"},
        )
        
        assert result.payload.get("_context") == {"user_id": "u123"}


class TestSignCheckpoint:
    """Test sign_checkpoint function."""
    
    def test_sign_checkpoint_dict(self):
        """Sign a checkpoint from dict."""
        checkpoint = {
            "thread_id": "thread_123",
            "checkpoint_ns": "",
            "values": {"key": "value"},
        }
        
        result = sign_checkpoint(checkpoint, agent_id="test-graph")
        
        assert result.payload["type"] == "checkpoint"
        assert result.payload["thread_id"] == "thread_123"
    
    def test_sign_checkpoint_with_id(self):
        """Sign checkpoint with explicit ID."""
        checkpoint = {"values": {"state": "data"}}
        
        result = sign_checkpoint(
            checkpoint,
            agent_id="test-graph",
            checkpoint_id="cp_123",
        )
        
        assert result.payload["checkpoint_id"] == "cp_123"


class TestSignStateTransition:
    """Test sign_state_transition function."""
    
    def test_sign_state_transition(self):
        """Sign a state transition."""
        from_state = {"step": 1}
        to_state = {"step": 2}
        
        result = sign_state_transition(
            from_state,
            to_state,
            agent_id="test-graph",
        )
        
        assert result.payload["type"] == "state_transition"
        assert result.payload["from_state"] == {"step": 1}
        assert result.payload["to_state"] == {"step": 2}
    
    def test_sign_state_transition_with_nodes(self):
        """Sign transition with node names."""
        result = sign_state_transition(
            {"a": 1},
            {"b": 2},
            agent_id="test-graph",
            from_node="step1",
            to_node="step2",
        )
        
        assert result.payload["from_node"] == "step1"
        assert result.payload["to_node"] == "step2"
    
    def test_sign_state_transition_excludes_moss_envelope(self):
        """Transition signing excludes moss_envelope from states."""
        from_state = {"data": "old", "moss_envelope": {"old": "env"}}
        to_state = {"data": "new", "moss_envelope": {"new": "env"}}
        
        result = sign_state_transition(
            from_state,
            to_state,
            agent_id="test-graph",
        )
        
        assert "moss_envelope" not in result.payload["from_state"]
        assert "moss_envelope" not in result.payload["to_state"]


class TestVerifyEnvelope:
    """Test verify_envelope function."""
    
    def test_verify_signed_envelope(self):
        """Verify a signed envelope."""
        state = {"result": "test"}
        sign_result = sign_node_output(state, agent_id="test-graph")
        
        verify_result = verify_envelope(sign_result.envelope)
        
        assert verify_result.valid is True
