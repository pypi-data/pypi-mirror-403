"""
Gather SDK - Connect Google ADK agents to Gather.is workspaces

Architecture:
    User (Web UI) → Tinode → GatherSDK → ADK Web Server → Gemini
                        ↑                      ↓
                Response sent back ← Response extracted

The SDK acts as a bridge between Tinode (chat) and ADK (agent runtime).
This enables full ADK debugging and session management while integrating
with Gather.is real-time chat infrastructure.

Usage:
    # Terminal 1: Start ADK web server for debugging
    adk web --port 8000

    # Terminal 2: Start the SDK bridge
    gathersdk serve --adk-url http://localhost:8000

    # Debug agents at: http://localhost:8000
"""

from .sdk import AgencySDK, SDKConfig, AgentConfig
from .discovery import discover_agents, DiscoveredAgent
from .client import TinodeClient, Message

__version__ = "0.2.0"
__all__ = [
    "AgencySDK",
    "SDKConfig",
    "AgentConfig",
    "discover_agents",
    "DiscoveredAgent",
    "TinodeClient",
    "Message",
]
