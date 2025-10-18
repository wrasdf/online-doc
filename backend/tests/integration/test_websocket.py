"""
Integration tests for WebSocket connection and message broadcasting.

Tests the real-time collaboration functionality including:
- WebSocket connection with JWT authentication
- Message broadcasting between multiple clients
- Yjs CRDT update synchronization
- Awareness (cursor/presence) updates
"""

import asyncio
import json
import base64
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app
from tests.utils.user import create_test_user, login_test_user
from tests.utils.document import create_test_document


@pytest.mark.asyncio
async def test_websocket_connection_with_valid_token(client: AsyncClient):
    """Test WebSocket connection succeeds with valid JWT token."""
    # Create user and document
    user = await create_test_user(client, "alice@test.com", "password123")
    token = await login_test_user(client, "alice@test.com", "password123")
    document = await create_test_document(client, token, "Test Document", "Initial content")

    # Connect to WebSocket
    with TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token}"
    ) as websocket:
        # Expect user_joined message
        data = websocket.receive_json()
        assert data["type"] == "user_joined"
        assert data["user"]["user_id"] == user["id"]


@pytest.mark.asyncio
async def test_websocket_connection_without_token_fails(client: AsyncClient):
    """Test WebSocket connection fails without JWT token."""
    # Create document
    user = await create_test_user(client, "bob@test.com", "password123")
    token = await login_test_user(client, "bob@test.com", "password123")
    document = await create_test_document(client, token, "Test Document", "Initial content")

    # Try to connect without token
    with pytest.raises(Exception):  # Should raise connection error
        with TestClient(app).websocket_connect(
            f"/ws/documents/{document['id']}"
        ) as websocket:
            pass


@pytest.mark.asyncio
async def test_websocket_sync_flow(client: AsyncClient):
    """Test complete sync flow: sync_step1 -> sync_step2."""
    # Setup
    user = await create_test_user(client, "charlie@test.com", "password123")
    token = await login_test_user(client, "charlie@test.com", "password123")
    document = await create_test_document(client, token, "Test Document", "Initial content")

    with TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token}"
    ) as websocket:
        # Receive user_joined
        websocket.receive_json()

        # Send sync_step1 to request document state
        websocket.send_json({
            "type": "sync_step1",
            "document_id": document["id"]
        })

        # Expect sync_step2 response with document state
        response = websocket.receive_json()
        assert response["type"] == "sync_step2"
        assert response["document_id"] == document["id"]
        assert "state" in response  # Base64 encoded Yjs state
        assert "version" in response


@pytest.mark.asyncio
async def test_websocket_broadcast_updates_to_multiple_clients(client: AsyncClient):
    """Test that updates from one client are broadcast to all other clients."""
    # Create user and document
    user = await create_test_user(client, "dave@test.com", "password123")
    token = await login_test_user(client, "dave@test.com", "password123")
    document = await create_test_document(client, token, "Shared Doc", "")

    # Create second user with access
    user2 = await create_test_user(client, "eve@test.com", "password123")
    token2 = await login_test_user(client, "eve@test.com", "password123")

    # Share document with user2
    share_response = await client.post(
        f"/api/v1/documents/{document['id']}/share",
        json={"email": "eve@test.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert share_response.status_code == 200

    # Connect both clients
    with TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token}"
    ) as ws1, TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token2}"
    ) as ws2:
        # Clear initial messages
        ws1.receive_json()  # user_joined for user1
        ws2.receive_json()  # user_joined for user2
        ws1.receive_json()  # user_joined for user2 (broadcast to user1)

        # Client 1 sends an update
        fake_yjs_update = base64.b64encode(b"fake_yjs_update_data").decode("utf-8")
        ws1.send_json({
            "type": "sync_update",
            "document_id": document["id"],
            "update": fake_yjs_update
        })

        # Client 2 should receive the broadcast update
        broadcast = ws2.receive_json()
        assert broadcast["type"] == "sync_update"
        assert broadcast["document_id"] == document["id"]
        assert broadcast["update"] == fake_yjs_update
        assert broadcast["user_id"] == user["id"]
        assert "timestamp" in broadcast


@pytest.mark.asyncio
async def test_websocket_awareness_updates(client: AsyncClient):
    """Test cursor position and awareness updates are broadcast."""
    # Setup
    user = await create_test_user(client, "frank@test.com", "password123")
    token = await login_test_user(client, "frank@test.com", "password123")
    document = await create_test_document(client, token, "Awareness Test", "")

    user2 = await create_test_user(client, "grace@test.com", "password123")
    token2 = await login_test_user(client, "grace@test.com", "password123")

    # Share document
    await client.post(
        f"/api/v1/documents/{document['id']}/share",
        json={"email": "grace@test.com"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Connect both clients
    with TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token}"
    ) as ws1, TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token2}"
    ) as ws2:
        # Clear initial messages
        ws1.receive_json()  # user_joined
        ws2.receive_json()  # user_joined
        ws1.receive_json()  # user2 joined broadcast

        # Client 1 sends awareness update
        ws1.send_json({
            "type": "awareness_update",
            "document_id": document["id"],
            "awareness": {
                "user_id": user["id"],
                "username": "frank@test.com",
                "cursor_position": 42,
                "cursor_color": "#FF5733",
                "selection_start": 42,
                "selection_end": 50
            }
        })

        # Client 2 should receive awareness update
        awareness = ws2.receive_json()
        assert awareness["type"] == "awareness_update"
        assert awareness["document_id"] == document["id"]
        assert awareness["awareness"]["cursor_position"] == 42
        assert awareness["awareness"]["cursor_color"] == "#FF5733"


@pytest.mark.asyncio
async def test_websocket_user_left_notification(client: AsyncClient):
    """Test that user_left message is broadcast when user disconnects."""
    # Setup
    user = await create_test_user(client, "henry@test.com", "password123")
    token = await login_test_user(client, "henry@test.com", "password123")
    document = await create_test_document(client, token, "User Leave Test", "")

    user2 = await create_test_user(client, "iris@test.com", "password123")
    token2 = await login_test_user(client, "iris@test.com", "password123")

    # Share document
    await client.post(
        f"/api/v1/documents/{document['id']}/share",
        json={"email": "iris@test.com"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Connect client 1
    with TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token}"
    ) as ws1:
        ws1.receive_json()  # user_joined

        # Connect and disconnect client 2
        with TestClient(app).websocket_connect(
            f"/ws/documents/{document['id']}?token={token2}"
        ) as ws2:
            ws2.receive_json()  # user_joined
            ws1.receive_json()  # user2 joined broadcast

        # After ws2 disconnects, ws1 should receive user_left
        user_left = ws1.receive_json()
        assert user_left["type"] == "user_left"
        assert user_left["user_id"] == user2["id"]
        assert user_left["username"] == "iris@test.com"
        assert "timestamp" in user_left


@pytest.mark.asyncio
async def test_websocket_connection_to_unshared_document_fails(client: AsyncClient):
    """Test that users cannot connect to documents they don't have access to."""
    # Create user1 and document
    user1 = await create_test_user(client, "jack@test.com", "password123")
    token1 = await login_test_user(client, "jack@test.com", "password123")
    document = await create_test_document(client, token1, "Private Doc", "")

    # Create user2 (no access to document)
    user2 = await create_test_user(client, "kelly@test.com", "password123")
    token2 = await login_test_user(client, "kelly@test.com", "password123")

    # User2 tries to connect to user1's document
    with pytest.raises(Exception):  # Should raise 4003 Forbidden
        with TestClient(app).websocket_connect(
            f"/ws/documents/{document['id']}?token={token2}"
        ) as websocket:
            # Should not reach here
            pass


@pytest.mark.asyncio
async def test_websocket_ping_pong_heartbeat(client: AsyncClient):
    """Test WebSocket heartbeat mechanism (ping-pong)."""
    # Setup
    user = await create_test_user(client, "leo@test.com", "password123")
    token = await login_test_user(client, "leo@test.com", "password123")
    document = await create_test_document(client, token, "Heartbeat Test", "")

    with TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token}"
    ) as websocket:
        websocket.receive_json()  # user_joined

        # Server should send ping periodically (we'll simulate)
        # In real implementation, server sends ping every 30 seconds
        websocket.send_json({"type": "pong"})

        # Connection should remain open
        # If no pong received within 10s, server would close connection


@pytest.mark.asyncio
async def test_websocket_concurrent_updates_from_multiple_users(client: AsyncClient):
    """Test that concurrent updates from multiple users are properly broadcast."""
    # Setup
    user1 = await create_test_user(client, "mike@test.com", "password123")
    token1 = await login_test_user(client, "mike@test.com", "password123")
    document = await create_test_document(client, token1, "Concurrent Test", "")

    user2 = await create_test_user(client, "nancy@test.com", "password123")
    token2 = await login_test_user(client, "nancy@test.com", "password123")

    user3 = await create_test_user(client, "oscar@test.com", "password123")
    token3 = await login_test_user(client, "oscar@test.com", "password123")

    # Share with all users
    await client.post(
        f"/api/v1/documents/{document['id']}/share",
        json={"email": "nancy@test.com"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    await client.post(
        f"/api/v1/documents/{document['id']}/share",
        json={"email": "oscar@test.com"},
        headers={"Authorization": f"Bearer {token1}"}
    )

    # Connect all three clients
    with TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token1}"
    ) as ws1, TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token2}"
    ) as ws2, TestClient(app).websocket_connect(
        f"/ws/documents/{document['id']}?token={token3}"
    ) as ws3:
        # Clear initial messages
        for ws in [ws1, ws2, ws3]:
            ws.receive_json()  # own user_joined

        # Clear broadcast messages
        ws1.receive_json()  # user2 joined
        ws1.receive_json()  # user3 joined
        ws2.receive_json()  # user3 joined

        # Each user sends an update
        update1 = base64.b64encode(b"update_from_user1").decode("utf-8")
        update2 = base64.b64encode(b"update_from_user2").decode("utf-8")
        update3 = base64.b64encode(b"update_from_user3").decode("utf-8")

        ws1.send_json({
            "type": "sync_update",
            "document_id": document["id"],
            "update": update1
        })
        ws2.send_json({
            "type": "sync_update",
            "document_id": document["id"],
            "update": update2
        })
        ws3.send_json({
            "type": "sync_update",
            "document_id": document["id"],
            "update": update3
        })

        # Each client should receive updates from the other two
        # ws1 should receive updates from ws2 and ws3
        received_updates = []
        for _ in range(2):
            msg = ws1.receive_json()
            assert msg["type"] == "sync_update"
            received_updates.append(msg["update"])

        assert update2 in received_updates
        assert update3 in received_updates
        assert update1 not in received_updates  # Should not receive own update
