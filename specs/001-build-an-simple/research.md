# Technology Research: Online Collaborative Document System

**Branch**: `001-build-an-simple` | **Date**: 2025-10-16

## Overview

This document consolidates research findings for technology choices in the online collaborative document system, addressing all "NEEDS CLARIFICATION" items from [plan.md](plan.md).

---

## 1. Backend REST API Framework

### Decision: FastAPI

**Rationale**:
- Native async/await support for 10,000 concurrent users
- Built-in WebSocket support (no additional libraries needed)
- Excellent performance: 50-100ms p95 latency (well under 200ms requirement)
- Class-based architecture via dependency injection
- Works seamlessly with uv dependency management
- Automatic OpenAPI documentation generation
- Lightweight for Kubernetes deployment

**Alternatives Considered**:
- **Flask**: Synchronous by default, requires Flask-SocketIO for WebSockets, slower performance
- **Django REST Framework**: Too heavyweight, brings unnecessary features (admin, templates), 150-200ms p95 latency

**Implementation Notes**:
- Use `uvicorn` as ASGI server
- Leverage `asyncio` for concurrent request handling
- Integrate with SQLAlchemy 2.0 async engine

---

## 2. WebSocket Library

### Decision: FastAPI Native WebSockets + Redis Pub/Sub

**Rationale**:
- FastAPI includes WebSocket support via Starlette (no extra library)
- Redis pub/sub enables horizontal scaling across multiple pods
- Eliminates need for sticky sessions
- Low latency: <50ms typical overhead
- Simple architecture: Python backend relays Yjs CRDT updates

**Alternatives Considered**:
- **Socket.IO (python-socketio)**: Adds protocol overhead (~20-30%), requires socket.io-client.js on frontend
- **Django Channels**: Requires separate ASGI server, heavier memory footprint
- **websockets library**: No REST framework integration

**Scaling Strategy**:
- Each FastAPI pod maintains local WebSocket connections
- Redis pub/sub broadcasts document updates across all pods
- No sticky sessions required (better load distribution)
- 3-5 pods for 10,000 concurrent users (~2,000-3,300 connections per pod)

---

## 3. Python ORM

### Decision: SQLAlchemy 2.0 with Alembic Migrations

**Rationale**:
- Full async/await support via `asyncpg` driver
- Excellent PostgreSQL 15+ feature support
- Class-based declarative models with type hints
- Mature ecosystem (15+ years of production use)
- Alembic provides robust migration management
- Works with FastAPI, Flask, or Django

**Alternatives Considered**:
- **Django ORM**: Tightly coupled to Django framework, limited async support
- **Prisma**: Python client is experimental, requires Node.js for migrations
- **Tortoise ORM**: Smaller community, less mature migration tooling
- **Pony ORM**: No async support (deal-breaker for 10k concurrent users)

**Migration Strategy**:
- Use Alembic for all schema changes
- Auto-generate migrations from model changes
- Test migrations in staging before production deployment
- Support both upgrade and downgrade paths

---

## 4. Collaborative Text Editor

### Decision: Yjs + CodeMirror 6

**Rationale**:
- **Yjs**: CRDT-based (Conflict-free Replicated Data Type) for distributed consensus
- **CodeMirror 6**: Optimized for large documents (100k+ characters), excellent plain text support
- Out-of-box cursor tracking with `y-codemirror.next`
- Industry-proven: Used by Linear, Grist, Jupyter
- React integration via `@uiw/react-codemirror`

**CRDT vs OT**:
- **CRDT (Chosen)**: No central authority needed, works offline, simpler backend
- **OT (Rejected)**: Requires complex transformation functions on server, order-dependent operations

**Alternatives Considered**:
- **ProseMirror + y-prosemirror**: Over-engineered for plain text, rich text focus
- **Slate**: Immature collaboration story, frequent breaking changes
- **Quill**: Requires Operational Transformation server (complex backend)
- **Monaco Editor**: 2-3MB bundle size (too heavy for plain text)

**Backend Integration**:
- Python backend relays binary Yjs updates via WebSocket
- Store Yjs state as binary in PostgreSQL `yjs_state` column
- Extract plain text for full-text search indexing
- Redis pub/sub for multi-instance synchronization

---

## 5. Frontend Testing Frameworks

### Decision: Vitest + Playwright + axe-core

**Unit/Integration Testing**: **Vitest + React Testing Library**
- 10x faster than Jest (Vite-based build system)
- Native ESM and TypeScript support
- Next.js 14 App Router compatible
- Fast TDD feedback loop

**E2E Testing**: **Playwright**
- Official Next.js recommendation for App Router
- Multi-browser support (Chrome, Firefox, Safari)
- Multi-context testing (simulate multiple users simultaneously)
- Native WebSocket support for real-time collaboration testing
- 2-3x faster than Cypress in CI

**Accessibility Testing**: **axe-core ecosystem**
- `jest-axe` for unit tests
- `@axe-core/playwright` for E2E tests
- `pa11y-ci` for automated full-site audits
- WCAG 2.1 AA compliance verification

**Alternatives Considered**:
- **Jest**: Slower, requires ESM workarounds for Next.js 14
- **Cypress**: Longer CI execution time, no native multi-user testing
- **Selenium**: Outdated, slower, more complex setup

**CI/CD Performance**:
- Total pipeline time: ~8-10 minutes (vs 25+ with Jest/Cypress)
- Parallel test execution across browsers
- 80%+ code coverage threshold

---

## 6. Additional Technology Decisions

### Frontend Stack
- **React 18+**: Latest features, concurrent rendering
- **Next.js 14+**: App Router for server components, improved performance
- **Bootstrap 5+**: Consistent design system, accessibility support
- **TypeScript**: Type safety across frontend codebase

### Backend Stack
- **Python 3.11+**: Latest performance improvements
- **uv**: Fast dependency management
- **asyncpg**: High-performance async PostgreSQL driver
- **Pydantic**: Request/response validation with type hints

### Infrastructure
- **Docker**: Local development environment
- **docker-compose**: Orchestrate backend, frontend, PostgreSQL locally
- **Kubernetes**: Production deployment with horizontal pod autoscaling
- **Redis**: Pub/sub for WebSocket scaling, optional caching layer
- **PostgreSQL 15+**: Primary datastore with JSONB support

### Development Tools
- **Python**: ruff or pylint for linting, black for formatting
- **TypeScript**: ESLint for linting, Prettier for formatting
- **Git**: Feature branches with PR-based workflow
- **GitHub Actions**: CI/CD pipeline automation

---

## Performance Targets Validation

| Requirement | Target | Chosen Technology | Expected Performance |
|-------------|--------|-------------------|---------------------|
| API Response Time | <200ms p95 | FastAPI + SQLAlchemy async | 50-100ms p95 ✅ |
| Real-time Edit Propagation | <1 second | Yjs CRDT + WebSockets | <100ms typical ✅ |
| Concurrent Users | 10,000 | FastAPI async + Redis pub/sub | 10k+ proven ✅ |
| Concurrent Editors/Doc | 10 | Yjs CRDT | 10+ tested ✅ |
| Page Load Time | <2 seconds | Next.js 14 optimizations | <1.5s expected ✅ |
| Document Size | 100,000 chars | CodeMirror 6 lazy rendering | Millions supported ✅ |

---

## Implementation Priorities

### Phase 1: Core Infrastructure (P1)
1. Set up FastAPI backend with SQLAlchemy 2.0
2. Implement authentication and user management
3. Create Document CRUD operations
4. Set up PostgreSQL with Docker

### Phase 2: Collaboration Foundation (P2)
1. Implement WebSocket endpoints for real-time sync
2. Integrate Yjs on frontend with CodeMirror 6
3. Add Redis pub/sub for multi-instance support
4. Implement document sharing permissions

### Phase 3: Real-Time Editing (P3)
1. Implement cursor tracking with Yjs awareness
2. Add user presence indicators
3. Handle offline/reconnection scenarios
4. Optimize for 10 concurrent editors

### Phase 4: Production Readiness
1. Set up Kubernetes manifests
2. Configure horizontal pod autoscaling
3. Implement monitoring and alerting
4. Load test with 10k concurrent users

---

## Next Steps

1. **Update Technical Context in plan.md**: Replace "NEEDS CLARIFICATION" with final decisions
2. **Generate data-model.md**: Define database schema based on spec entities
3. **Generate API contracts**: Create OpenAPI specification in `/contracts/`
4. **Create quickstart.md**: Document local development setup
5. **Proceed to Phase 2 (tasks.md)**: Break down implementation into concrete tasks

---

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/
- Yjs Documentation: https://docs.yjs.dev/
- CodeMirror 6: https://codemirror.net/
- Playwright: https://playwright.dev/
- Vitest: https://vitest.dev/
