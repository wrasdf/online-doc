"""WebSocket API package for real-time collaboration."""

from .handler import websocket_endpoint, ConnectionManager, manager

__all__ = ["websocket_endpoint", "ConnectionManager", "manager"]
