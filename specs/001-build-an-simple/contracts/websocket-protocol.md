# WebSocket Protocol Specification

**Version**: 1.0.0
**Last Updated**: 2025-10-16

## Overview

The WebSocket protocol enables real-time collaborative editing by synchronizing Yjs CRDT updates and awareness information (cursors, presence) between clients via the Python backend.

---

## Connection

### Endpoint
```
ws://localhost:8000/ws/documents/{documentId}?token={jwt_token}
```

**Production**:
```
wss://api.online-doc.example.com/ws/documents/{documentId}?token={jwt_token}
```

### Authentication
- JWT token passed as query parameter: `?token=<access_token>`
- Token validated on connection
- Connection closed with code `4003` (Forbidden) if invalid

### Connection Lifecycle
```
Client connects → Server validates token → Server sends initial state → Client syncs → Bidirectional messages
```

---

## Message Format

All messages are JSON objects with a `type` field:

```json
{
  "type": "<message_type>",
  ...additional fields
}
```

---

## Message Types

### 1. Client → Server Messages

#### 1.1 `sync_step1` - Request Document State
Sent by client after connection to request current document state.

```json
{
  "type": "sync_step1",
  "document_id": "uuid"
}
```

**Response**: Server sends `sync_step2` with current Yjs state

---

#### 1.2 `sync_update` - Send Document Update
Sent when client makes local changes (Yjs update).

```json
{
  "type": "sync_update",
  "document_id": "uuid",
  "update": "base64_encoded_yjs_update"
}
```

**Server Action**:
- Broadcast update to all other connected clients
- Optionally persist to database (debounced auto-save)

---

#### 1.3 `awareness_update` - Send Cursor/Presence
Sent when cursor position or user presence changes.

```json
{
  "type": "awareness_update",
  "document_id": "uuid",
  "awareness": {
    "user_id": "uuid",
    "username": "string",
    "cursor_position": 123,
    "cursor_color": "#FF5733",
    "selection_start": 123,
    "selection_end": 130
  }
}
```

**Server Action**:
- Broadcast awareness update to all other connected clients
- Update `edit_sessions` table with latest cursor position

---

### 2. Server → Client Messages

#### 2.1 `sync_step2` - Send Initial Document State
Sent in response to `sync_step1`, provides current Yjs document state.

```json
{
  "type": "sync_step2",
  "document_id": "uuid",
  "state": "base64_encoded_yjs_state",
  "version": 42
}
```

**Client Action**:
- Apply Yjs state to local document
- Client is now in sync with server

---

#### 2.2 `sync_update` - Broadcast Document Update
Broadcast when another user makes changes.

```json
{
  "type": "sync_update",
  "document_id": "uuid",
  "update": "base64_encoded_yjs_update",
  "user_id": "uuid",
  "timestamp": "2025-10-16T10:30:00Z"
}
```

**Client Action**:
- Apply Yjs update to local document
- Yjs CRDT ensures conflict-free merging

---

#### 2.3 `awareness_update` - Broadcast Cursor/Presence
Broadcast when another user's cursor moves or presence changes.

```json
{
  "type": "awareness_update",
  "document_id": "uuid",
  "awareness": {
    "user_id": "uuid",
    "username": "Alice",
    "cursor_position": 456,
    "cursor_color": "#00BFFF",
    "selection_start": null,
    "selection_end": null
  }
}
```

**Client Action**:
- Update cursor indicator for that user
- Show username label next to cursor

---

#### 2.4 `user_joined` - User Connected
Sent when a new user connects to the document.

```json
{
  "type": "user_joined",
  "document_id": "uuid",
  "user": {
    "user_id": "uuid",
    "username": "Bob",
    "cursor_color": "#32CD32"
  },
  "timestamp": "2025-10-16T10:30:00Z"
}
```

**Client Action**:
- Display notification: "Bob joined"
- Initialize cursor indicator for Bob

---

#### 2.5 `user_left` - User Disconnected
Sent when a user disconnects from the document.

```json
{
  "type": "user_left",
  "document_id": "uuid",
  "user_id": "uuid",
  "username": "Bob",
  "timestamp": "2025-10-16T10:35:00Z"
}
```

**Client Action**:
- Display notification: "Bob left"
- Remove cursor indicator for Bob

---

#### 2.6 `error` - Error Message
Sent when an error occurs.

```json
{
  "type": "error",
  "error": "permission_denied",
  "message": "You do not have permission to edit this document",
  "code": 403
}
```

**Client Action**:
- Display error message to user
- Optionally reconnect or close connection

---

#### 2.7 `server_shutdown` - Server Maintenance
Sent when server is shutting down (graceful pod termination in Kubernetes).

```json
{
  "type": "server_shutdown",
  "message": "Server restarting, please reconnect",
  "reconnect": true
}
```

**Client Action**:
- Close connection gracefully
- Attempt reconnection after delay (exponential backoff)

---

## Connection Management

### Heartbeat / Ping-Pong
To detect dead connections:

**Server sends** (every 30 seconds):
```json
{
  "type": "ping"
}
```

**Client responds**:
```json
{
  "type": "pong"
}
```

**Timeout**: If no `pong` received within 10 seconds, server closes connection.

---

### Reconnection Strategy (Client)

When connection is lost:

1. **Exponential Backoff**: Wait 1s, 2s, 4s, 8s, 16s (max 30s)
2. **Retry**: Attempt reconnection with same JWT token
3. **Re-sync**: On successful reconnection, send `sync_step1` to get latest state
4. **Queue Local Changes**: While offline, queue Yjs updates locally
5. **Sync on Reconnect**: Send queued updates when connection restored

---

### Connection Closure Codes

| Code | Reason | Description |
|------|--------|-------------|
| `1000` | Normal Closure | Client closed connection normally |
| `1001` | Going Away | Server shutting down (graceful) |
| `1008` | Policy Violation | Authentication failed |
| `1011` | Internal Error | Server error occurred |
| `4003` | Forbidden | User does not have access to document |
| `4004` | Document Not Found | Document ID does not exist |

---

## Example Flow: Two Users Editing

### Initial Connection (User A)

1. **User A connects**:
   ```
   Client A → Server: WebSocket connection + JWT token
   ```

2. **Server validates and responds**:
   ```
   Server → Client A: user_joined (for User A)
   ```

3. **Client A requests state**:
   ```
   Client A → Server: sync_step1
   ```

4. **Server sends current state**:
   ```
   Server → Client A: sync_step2 (Yjs state)
   ```

---

### User B Joins

1. **User B connects**:
   ```
   Client B → Server: WebSocket connection + JWT token
   Server → Client B: user_joined (for User B)
   Server → Client A: user_joined (for User B)  // Notify User A
   ```

2. **Client B syncs**:
   ```
   Client B → Server: sync_step1
   Server → Client B: sync_step2 (Yjs state)
   ```

---

### Collaborative Editing

1. **User A types "Hello"**:
   ```
   Client A → Server: sync_update (Yjs update for "Hello" insertion)
   Server → Client B: sync_update (broadcast to User B)
   Client B applies update → sees "Hello"
   ```

2. **User B types " World" at end**:
   ```
   Client B → Server: sync_update (Yjs update for " World" insertion)
   Server → Client A: sync_update (broadcast to User A)
   Client A applies update → sees "Hello World"
   ```

3. **Cursor tracking**:
   ```
   Client A moves cursor to position 5
   Client A → Server: awareness_update (cursor_position: 5)
   Server → Client B: awareness_update
   Client B shows User A's cursor at position 5
   ```

---

## Security Considerations

1. **Authentication**: JWT token required for all connections
2. **Authorization**: Verify user has access to document before accepting connection
3. **Rate Limiting**: Limit messages per second per connection (e.g., 100 msg/s)
4. **Message Size**: Limit maximum message size (e.g., 1MB)
5. **Connection Limits**: Limit concurrent connections per user (e.g., 10)

---

## Performance Optimizations

1. **Binary Format**: Use binary WebSocket messages for Yjs updates (more efficient than JSON)
2. **Compression**: Enable WebSocket per-message compression
3. **Batching**: Batch multiple small updates into single message
4. **Debouncing**: Debounce cursor position updates (max 10 updates/second)

---

## Error Handling

### Network Interruption
- Client queues local changes
- Client attempts reconnection with exponential backoff
- On reconnect, client sends queued updates

### Concurrent Edits Conflict
- Yjs CRDT handles automatically
- No manual conflict resolution needed

### Server Error
- Server sends `error` message
- Client displays error notification
- Client attempts reconnection

---

## Testing Scenarios

1. **Single User**: User connects, edits, saves → verify persistence
2. **Two Users**: Users A and B edit simultaneously → verify real-time sync
3. **Ten Users**: 10 concurrent editors → verify performance (FR-016)
4. **Network Interruption**: Disconnect client mid-edit → verify offline queue and sync on reconnect
5. **Server Restart**: Gracefully close connections → verify client reconnection
6. **Large Document**: 100k character document → verify performance (SC-009)

---

## References

- Yjs Protocol: https://docs.yjs.dev/api/y.doc#syncing
- WebSocket RFC: https://datatracker.ietf.org/doc/html/rfc6455
- y-websocket provider: https://github.com/yjs/y-websocket
