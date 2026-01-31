"""Checkpoint client module.

This module provides the low-level HTTP client for checkpoint operations.
For the LangGraph-compatible checkpointer, see march_agent.extensions.langgraph.

Usage:
    from march_agent.extensions.langgraph import HTTPCheckpointSaver

    app = MarchAgentApp(gateway_url="agent-gateway:8080", api_key="key")
    checkpointer = HTTPCheckpointSaver(app=app)
"""

# Re-export CheckpointClient for backwards compatibility
from .checkpoint_client import CheckpointClient

__all__ = ["CheckpointClient"]
