# Tasks: Online Collaborative Document System

**Input**: Design documents from `/specs/001-build-an-simple/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as per the Test-First Development principle in the constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend project structure in `backend/`
- [ ] T002 Create frontend project structure in `frontend/`
- [ ] T003 Initialize Python project with uv in `backend/` and add dependencies from `plan.md` to `backend/pyproject.toml`
- [ ] T004 Initialize Next.js project in `frontend/` and add dependencies from `plan.md` to `frontend/package.json`
- [ ] T005 [P] Configure linting (ruff) and formatting (black) for backend in `backend/pyproject.toml`
- [ ] T006 [P] Configure linting (ESLint) and formatting (Prettier) for frontend in `frontend/.eslintrc.json` and `frontend/.prettierrc`
- [ ] T007 [P] Create `docker-compose.yml` for local development with `postgres`, `redis`, `backend`, and `frontend` services as defined in `quickstart.md`
- [ ] T008 [P] Create `Dockerfile` for backend service in `backend/Dockerfile`
- [ ] T009 [P] Create `Dockerfile` for frontend service in `frontend/Dockerfile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 Setup database connection and session management in `backend/src/db/session.py`
- [ ] T011 Configure Alembic for database migrations in `backend/alembic/`
- [ ] T012 Implement User model in `backend/src/models/user.py` and generate initial migration
- [ ] T013 Implement Document model in `backend/src/models/document.py` and generate migration
- [ ] T014 Implement authentication service for user registration and login in `backend/src/services/user_service.py`
- [ ] T015 Implement JWT token generation and validation in `backend/src/services/auth_service.py`
- [ ] T016 [P] Create authentication middleware in `backend/src/middleware/auth.py`
- [ ] T017 [P] Setup API routing and middleware structure in `backend/src/main.py`
- [ ] T018 [P] Create Pydantic schemas for User and Auth in `backend/src/schemas/user.py`
- [ ] T019 [P] Setup basic frontend layout with Next.js App Router in `frontend/src/app/layout.tsx`
- [ ] T020 [P] Setup API client service in `frontend/src/services/api.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create and Edit Personal Document (Priority: P1) 🎯 MVP

**Goal**: A user can create, edit, and manage their own documents.

**Independent Test**: A single user can register, log in, create a document, edit it, see it in their document list, and have their changes persist.

### Tests for User Story 1 ⚠️

- [ ] T021 [P] [US1] Contract test for `POST /documents` in `backend/tests/contract/test_documents.py`
- [ ] T022 [P] [US1] Integration test for creating and editing a document in `backend/tests/integration/test_document_flow.py`
- [ ] T023 [P] [US1] Unit test for `DocumentService` in `backend/tests/unit/test_document_service.py`
- [ ] T024 [P] [US1] E2E test for document creation flow in `frontend/tests/e2e/document-creation.spec.ts` using Playwright

### Implementation for User Story 1

- [ ] T025 [US1] Implement `DocumentService` for CRUD operations in `backend/src/services/document_service.py`
- [ ] T026 [US1] Implement API endpoints for documents (`/documents` and `/documents/{documentId}`) in `backend/src/api/routes/documents.py`
- [ ] T027 [US1] Create Pydantic schemas for Document in `backend/src/schemas/document.py`
- [ ] T028 [P] [US1] Create frontend page for listing documents at `frontend/src/app/documents/page.tsx`
- [ ] T029 [P] [US1] Create frontend page for viewing/editing a document at `frontend/src/app/documents/[id]/page.tsx`
- [ ] T030 [US1] Implement CodeMirror 6 editor component in `frontend/src/components/editor/CodeMirrorEditor.tsx`
- [ ] T031 [US1] Integrate document creation and editing functionality with the backend API

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Share Document for Collaboration (Priority: P2)

**Goal**: A document owner can share their document with other users for editing.

**Independent Test**: User A creates a document, shares it with User B. User B can see the shared document and edit it.

### Tests for User Story 2 ⚠️

- [ ] T032 [P] [US2] Contract test for `POST /documents/{documentId}/share` in `backend/tests/contract/test_sharing.py`
- [ ] T033 [P] [US2] Integration test for sharing a document in `backend/tests/integration/test_sharing_flow.py`
- [ ] T034 [P] [US2] E2E test for sharing a document in `frontend/tests/e2e/sharing.spec.ts`

### Implementation for User Story 2

- [ ] T035 [US2] Implement `DocumentAccess` model in `backend/src/models/document_access.py` and generate migration
- [ ] T036 [US2] Implement `SharingService` in `backend/src/services/sharing_service.py`
- [ ] T037 [US2] Implement API endpoints for sharing (`/documents/{documentId}/share`) in `backend/src/api/routes/sharing.py`
- [ ] T038 [US2] Create Pydantic schemas for Sharing in `backend/src/schemas/sharing.py`
- [ ] T039 [P] [US2] Create frontend UI for sharing documents in `frontend/src/components/sharing/ShareDialog.tsx`
- [ ] T040 [US2] Integrate sharing functionality with the backend API

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Real-Time Simultaneous Editing (Priority: P3)

**Goal**: Multiple users can edit the same document simultaneously and see each other's changes in real-time.

**Independent Test**: Two users open the same document and type at the same time, their changes should appear on each other's screen in real-time.

### Tests for User Story 3 ⚠️

- [ ] T041 [P] [US3] Integration test for WebSocket connection and message broadcasting in `backend/tests/integration/test_websocket.py`
- [ ] T042 [P] [US3] E2E test for real-time collaboration with two users in `frontend/tests/e2e/collaboration.spec.ts`

### Implementation for User Story 3

- [ ] T043 [US3] Implement `EditSession` and `Change` models in `backend/src/models/collaboration.py` and generate migrations
- [ ] T044 [US3] Implement WebSocket connection handler in `backend/src/api/websocket/handler.py`
- [ ] T045 [US3] Implement Redis pub/sub for broadcasting messages in `backend/src/services/collaboration_service.py`
- [ ] T046 [US3] Integrate Yjs on the frontend with the CodeMirror component and WebSocket service in `frontend/src/services/collaboration.ts`
- [ ] T047 [P] [US3] Implement cursor tracking and user presence indicators in `frontend/src/components/editor/Awareness.tsx`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates in `README.md` and `docs/`
- [ ] T049 Code cleanup and refactoring across `backend/` and `frontend/`
- [ ] T050 Performance optimization for database queries and WebSocket messages
- [ ] T051 Security hardening for all API endpoints
- [ ] T052 Run `quickstart.md` validation to ensure setup is smooth

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Depends on User Story 1
- **User Story 3 (P3)**: Depends on User Story 2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Setup + Foundational
2. Add User Story 1 → Test independently
3. Add User Story 2 → Test independently
4. Add User Story 3 → Test independently
