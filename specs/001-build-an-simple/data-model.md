# Data Model: Online Collaborative Document System

**Branch**: `001-build-an-simple` | **Date**: 2025-10-16
**Source**: Extracted from [spec.md](spec.md) Key Entities section

---

## Entity Relationship Diagram

```
┌─────────────┐         owns          ┌──────────────┐
│    User     │◄──────────────────────┤   Document   │
└─────────────┘                       └──────────────┘
       │                                      │
       │                                      │
       │ has_access                           │ has_changes
       │                                      │
       ▼                                      ▼
┌─────────────────┐                   ┌──────────────┐
│ DocumentAccess  │───────for────────►│   Change     │
└─────────────────┘                   └──────────────┘
       │
       │
       │ active_in
       ▼
┌─────────────────┐
│  EditSession    │
└─────────────────┘
```

---

## Entity Definitions

### 1. User

**Purpose**: Represents an authenticated person who can create and edit documents.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL | User's display name |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Email address (for sharing and authentication) |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password (bcrypt) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| `last_login` | TIMESTAMP | NULLABLE | Last successful login |

**Relationships**:
- **Owns**: One-to-many with Document (user can own multiple documents)
- **Has Access**: One-to-many with DocumentAccess (user can access multiple shared documents)
- **Active In**: One-to-many with EditSession (user can have active sessions in multiple documents)
- **Makes Changes**: One-to-many with Change (user creates document changes)

**Validation Rules**:
- Email must be valid format (RFC 5322)
- Username must be 3-100 characters, alphanumeric plus `-_`
- Password must be at least 8 characters (enforced at application layer)

**Indexes**:
```sql
CREATE UNIQUE INDEX idx_user_email ON users(email);
CREATE UNIQUE INDEX idx_user_username ON users(username);
```

---

### 2. Document

**Purpose**: Represents a collaborative text document with content, metadata, and ownership.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `title` | VARCHAR(255) | NOT NULL | Document title |
| `content` | TEXT | NOT NULL, DEFAULT '' | Plain text content (deprecated in favor of yjs_state) |
| `yjs_state` | BYTEA | NULLABLE | Binary Yjs CRDT state for collaborative editing |
| `owner_id` | UUID | FOREIGN KEY → User.id, NOT NULL | Document owner |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last modification timestamp |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | Version counter for optimistic locking |

**Relationships**:
- **Owned By**: Many-to-one with User (document has one owner)
- **Shared With**: One-to-many with DocumentAccess (document can be shared with multiple users)
- **Has Changes**: One-to-many with Change (document has history of changes)
- **Has Sessions**: One-to-many with EditSession (document has active edit sessions)

**Validation Rules**:
- Title must be 1-255 characters
- Content or yjs_state must be present (at least one)
- updated_at must be >= created_at

**State Transitions**:
```
[Created] → [Editing] → [Saved]
    │           │           │
    │           └──────────►[Shared] → [Collaborative Editing]
    │                                        │
    └────────────────────────────────────────►[Deleted]
```

**Indexes**:
```sql
CREATE INDEX idx_document_owner ON documents(owner_id);
CREATE INDEX idx_document_updated ON documents(updated_at DESC);
CREATE INDEX idx_document_title ON documents USING gin(to_tsvector('english', title));
```

---

### 3. DocumentAccess

**Purpose**: Represents sharing permissions linking users to documents they can access (beyond documents they own).

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `user_id` | UUID | FOREIGN KEY → User.id, NOT NULL | User granted access |
| `document_id` | UUID | FOREIGN KEY → Document.id, NOT NULL | Document being shared |
| `access_type` | ENUM | NOT NULL, DEFAULT 'editor' | Access level: 'owner' or 'editor' |
| `granted_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | When access was granted |
| `granted_by` | UUID | FOREIGN KEY → User.id, NOT NULL | Who granted the access |

**Relationships**:
- **User**: Many-to-one with User (who has access)
- **Document**: Many-to-one with Document (which document)
- **Granted By**: Many-to-one with User (who granted access)

**Validation Rules**:
- User cannot have duplicate access entries for same document
- access_type must be 'owner' or 'editor' (no view-only per FR-012)
- Only document owner can grant access (enforced at application layer)

**Constraints**:
```sql
ALTER TABLE document_access
  ADD CONSTRAINT unique_user_document UNIQUE (user_id, document_id);

ALTER TABLE document_access
  ADD CONSTRAINT valid_access_type CHECK (access_type IN ('owner', 'editor'));
```

**Indexes**:
```sql
CREATE INDEX idx_document_access_user ON document_access(user_id);
CREATE INDEX idx_document_access_document ON document_access(document_id);
CREATE UNIQUE INDEX idx_unique_user_document ON document_access(user_id, document_id);
```

---

### 4. EditSession

**Purpose**: Represents an active editing connection, tracking which users are currently viewing/editing which documents.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `user_id` | UUID | FOREIGN KEY → User.id, NOT NULL | User in session |
| `document_id` | UUID | FOREIGN KEY → Document.id, NOT NULL | Document being edited |
| `cursor_position` | INTEGER | NULLABLE | Current cursor position in document |
| `cursor_color` | VARCHAR(7) | NOT NULL | Hex color for user's cursor indicator |
| `connection_status` | ENUM | NOT NULL | Status: 'connected', 'idle', 'disconnected' |
| `started_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Session start time |
| `last_activity` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last cursor movement or edit |
| `websocket_id` | VARCHAR(255) | NULLABLE | WebSocket connection identifier |

**Relationships**:
- **User**: Many-to-one with User (who is editing)
- **Document**: Many-to-one with Document (which document)

**Validation Rules**:
- cursor_position must be >= 0
- cursor_color must be valid hex color (#RRGGBB)
- connection_status must be 'connected', 'idle', or 'disconnected'
- Session is considered inactive if last_activity > 5 minutes ago

**State Transitions**:
```
[Connected] → [Idle] → [Disconnected]
     │         │              │
     └─────────┴──────────────►[Reconnected] → [Connected]
```

**Constraints**:
```sql
ALTER TABLE edit_sessions
  ADD CONSTRAINT valid_connection_status
  CHECK (connection_status IN ('connected', 'idle', 'disconnected'));

ALTER TABLE edit_sessions
  ADD CONSTRAINT valid_cursor_position
  CHECK (cursor_position >= 0);
```

**Indexes**:
```sql
CREATE INDEX idx_edit_session_document ON edit_sessions(document_id);
CREATE INDEX idx_edit_session_user ON edit_sessions(user_id);
CREATE INDEX idx_edit_session_status ON edit_sessions(connection_status, last_activity);
```

---

### 5. Change

**Purpose**: Represents a single edit operation in a document. Used for real-time synchronization and potentially for version history.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `document_id` | UUID | FOREIGN KEY → Document.id, NOT NULL | Document being changed |
| `user_id` | UUID | FOREIGN KEY → User.id, NOT NULL | User who made the change |
| `operation_type` | ENUM | NOT NULL | Operation: 'insert', 'delete', 'update' |
| `position` | INTEGER | NOT NULL | Character position in document |
| `content` | TEXT | NULLABLE | Content being inserted (NULL for delete) |
| `length` | INTEGER | NULLABLE | Length of deletion (NULL for insert) |
| `yjs_update` | BYTEA | NULLABLE | Binary Yjs update for CRDT synchronization |
| `timestamp` | TIMESTAMP | NOT NULL, DEFAULT NOW() | When change occurred |
| `sequence_number` | BIGSERIAL | NOT NULL | Sequential ordering within document |

**Relationships**:
- **Document**: Many-to-one with Document (which document)
- **User**: Many-to-one with User (who made change)

**Validation Rules**:
- operation_type must be 'insert', 'delete', or 'update'
- position must be >= 0
- For 'insert': content must NOT be NULL
- For 'delete': length must be > 0
- sequence_number ensures total ordering of changes per document

**Constraints**:
```sql
ALTER TABLE changes
  ADD CONSTRAINT valid_operation_type
  CHECK (operation_type IN ('insert', 'delete', 'update'));

ALTER TABLE changes
  ADD CONSTRAINT valid_position
  CHECK (position >= 0);

ALTER TABLE changes
  ADD CONSTRAINT insert_has_content
  CHECK (operation_type != 'insert' OR content IS NOT NULL);

ALTER TABLE changes
  ADD CONSTRAINT delete_has_length
  CHECK (operation_type != 'delete' OR length > 0);
```

**Indexes**:
```sql
CREATE INDEX idx_change_document ON changes(document_id, sequence_number);
CREATE INDEX idx_change_timestamp ON changes(timestamp DESC);
CREATE INDEX idx_change_user ON changes(user_id);
```

---

## Database Schema (SQLAlchemy 2.0)

**File**: `/Users/ikerry/works/online-doc/backend/src/models/`

### Example: Document Model

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, LargeBinary, DateTime, Integer, ForeignKey
from datetime import datetime
from typing import List, Optional
import uuid

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Attributes
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    yjs_state: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Foreign Keys
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="owned_documents")
    accesses: Mapped[List["DocumentAccess"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan"
    )
    changes: Mapped[List["Change"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan"
    )
    edit_sessions: Mapped[List["EditSession"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title})>"
```

---

## Migration Plan

### Initial Schema Setup (Alembic)

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema: User, Document, DocumentAccess, EditSession, Change"

# Review migration file
# Edit if needed for data transformations

# Apply migration
alembic upgrade head
```

### Migration Order

1. **users** table (no dependencies)
2. **documents** table (depends on users)
3. **document_access** table (depends on users, documents)
4. **edit_sessions** table (depends on users, documents)
5. **changes** table (depends on users, documents)

---

## Performance Considerations

### Connection Pooling
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Base connection pool for 10k users
    max_overflow=40,     # Additional connections during spikes
    pool_pre_ping=True   # Verify connections before use
)
```

### Query Optimization
- Use eager loading for relationships to avoid N+1 queries
- Index foreign keys and frequently queried columns
- Use database-level caching for read-heavy operations

### Data Retention
- **Changes table**: Consider partitioning by timestamp or archiving old changes
- **EditSessions table**: Regularly clean up disconnected sessions > 24 hours old
- **Yjs state**: Periodically compact Yjs state to reduce storage size

---

## Next Steps

1. Implement SQLAlchemy models in `/backend/src/models/`
2. Create Alembic migrations
3. Set up database connection and session management
4. Generate API contracts based on these entities
5. Write unit tests for model validations

---

## References

- Spec entities: [spec.md](spec.md#key-entities)
- SQLAlchemy 2.0 docs: https://docs.sqlalchemy.org/en/20/
- PostgreSQL data types: https://www.postgresql.org/docs/15/datatype.html
