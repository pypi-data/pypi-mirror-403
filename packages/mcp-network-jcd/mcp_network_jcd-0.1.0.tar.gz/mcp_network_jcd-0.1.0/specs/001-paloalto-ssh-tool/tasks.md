# Tasks: Palo Alto SSH Query Tool

**Input**: Design documents from `/specs/001-paloalto-ssh-tool/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: Required per Constitution Principle II (Test-First Development - NON-NEGOTIABLE)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1, US2, US3)
- Exact file paths included

## Path Conventions

- **Source**: `src/mcp_network_jcd/`
- **Tests**: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Python package structure

- [x] T001 Create project directory structure per plan.md in src/mcp_network_jcd/
- [x] T002 Initialize Python 3.12 project with pyproject.toml (mcp, netmiko, pydantic dependencies)
- [x] T003 [P] Create src/mcp_network_jcd/__init__.py with package metadata
- [x] T004 [P] Create tests/conftest.py with shared pytest fixtures (mock credentials, mock netmiko)
- [x] T005 [P] Configure ruff for linting in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational (TDD - write first, must fail)

- [x] T006 [P] Unit test for ServerCredentials.from_env() in tests/unit/test_models.py
- [x] T007 [P] Unit test for DeviceConnection validation in tests/unit/test_models.py
- [x] T008 [P] Unit test for QueryRequest validation in tests/unit/test_models.py

### Implementation for Foundational

- [x] T009 [P] Create ServerCredentials model in src/mcp_network_jcd/models/paloalto.py
- [x] T010 [P] Create DeviceConnection model in src/mcp_network_jcd/models/paloalto.py
- [x] T011 [P] Create QueryRequest model in src/mcp_network_jcd/models/paloalto.py
- [x] T012 Create src/mcp_network_jcd/models/__init__.py with model exports
- [x] T013 Create FastMCP server skeleton in src/mcp_network_jcd/server.py (no tools yet)
- [x] T014 Create src/mcp_network_jcd/tools/__init__.py

**Checkpoint**: Foundation ready - models validated, server skeleton runs

---

## Phase 3: User Story 1 - Query Firewall Configuration (Priority: P1) 🎯 MVP

**Goal**: Execute a single command on a Palo Alto device and return structured output

**Independent Test**: Connect to device, run `show system info`, verify JSON response with hostname/version

### Tests for User Story 1 (TDD - write first, must fail)

- [x] T015 [P] [US1] Unit test for CommandResult model in tests/unit/test_models.py
- [x] T016 [P] [US1] Unit test for QueryResponse model in tests/unit/test_models.py
- [x] T017 [P] [US1] Contract test for paloalto_query tool (success case) in tests/contract/test_paloalto_tool.py
- [x] T018 [P] [US1] Integration test for SSH connection (mocked netmiko) in tests/integration/test_paloalto_ssh.py

### Implementation for User Story 1

- [x] T019 [P] [US1] Create CommandResult model in src/mcp_network_jcd/models/paloalto.py
- [x] T020 [P] [US1] Create DeviceInfo model in src/mcp_network_jcd/models/paloalto.py
- [x] T021 [P] [US1] Create QueryResponse model in src/mcp_network_jcd/models/paloalto.py
- [x] T022 [US1] Implement paloalto_query tool (single command) in src/mcp_network_jcd/tools/paloalto.py
  - **Note**: Handle SSH disconnection mid-command by returning partial output with error flag (see data-model.md)
- [x] T023 [US1] Register paloalto_query tool in src/mcp_network_jcd/server.py
- [x] T024 [US1] Add netmiko connection logic with host key skip in src/mcp_network_jcd/tools/paloalto.py

**Checkpoint**: US1 complete - single command query works, returns structured JSON

---

## Phase 4: User Story 2 - Handle Connection Failures Gracefully (Priority: P2)

**Goal**: Return clear error messages for auth failures, timeouts, connection refused

**Independent Test**: Attempt connection with invalid credentials, verify error code and message

### Tests for User Story 2 (TDD - write first, must fail)

- [x] T025 [P] [US2] Unit test for ErrorInfo model in tests/unit/test_models.py
- [x] T026 [P] [US2] Contract test for AUTH_FAILED error response in tests/contract/test_paloalto_tool.py
- [x] T027 [P] [US2] Contract test for CONNECTION_TIMEOUT error response in tests/contract/test_paloalto_tool.py
- [x] T028 [P] [US2] Contract test for CONNECTION_REFUSED error response in tests/contract/test_paloalto_tool.py
- [x] T029 [P] [US2] Contract test for CONFIG_ERROR (missing env vars) in tests/contract/test_paloalto_tool.py

### Implementation for User Story 2

- [x] T030 [US2] Create ErrorInfo model in src/mcp_network_jcd/models/paloalto.py
- [x] T031 [US2] Add exception mapping (netmiko → error codes) in src/mcp_network_jcd/tools/paloalto.py
- [x] T032 [US2] Handle NetMikoTimeoutException → CONNECTION_TIMEOUT in src/mcp_network_jcd/tools/paloalto.py
- [x] T033 [US2] Handle NetMikoAuthenticationException → AUTH_FAILED in src/mcp_network_jcd/tools/paloalto.py
- [x] T034 [US2] Handle SSHException → CONNECTION_REFUSED in src/mcp_network_jcd/tools/paloalto.py
- [x] T035 [US2] Handle missing credentials → CONFIG_ERROR in src/mcp_network_jcd/tools/paloalto.py

**Checkpoint**: US2 complete - all error scenarios return proper error codes and messages

---

## Phase 5: User Story 3 - Execute Multiple Commands (Priority: P3)

**Goal**: Execute batch of 1-10 commands in single request, return all results

**Independent Test**: Submit 3 commands, verify all 3 results returned with individual success/output

### Tests for User Story 3 (TDD - write first, must fail)

- [x] T036 [P] [US3] Contract test for batch query (3 commands, all succeed) in tests/contract/test_paloalto_tool.py
- [x] T037 [P] [US3] Contract test for partial failure (1 of 3 fails) in tests/contract/test_paloalto_tool.py
- [x] T038 [P] [US3] Unit test for command list validation (1-10 limit) in tests/unit/test_models.py

### Implementation for User Story 3

- [x] T039 [US3] Refactor paloalto_query to iterate over commands list in src/mcp_network_jcd/tools/paloalto.py
- [x] T040 [US3] Aggregate CommandResult[] into QueryResponse.results in src/mcp_network_jcd/tools/paloalto.py
- [x] T041 [US3] Handle partial failures (continue on command error) in src/mcp_network_jcd/tools/paloalto.py
  - **Note**: If SSH disconnects mid-batch, return results collected so far with partial output on interrupted command
- [x] T042 [US3] Add duration_ms tracking per command in src/mcp_network_jcd/tools/paloalto.py

**Checkpoint**: US3 complete - batch queries work with partial failure handling

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation

- [x] T043 [P] Update src/mcp_network_jcd/models/__init__.py with all model exports
- [x] T044 [P] Add __all__ exports in src/mcp_network_jcd/tools/__init__.py
- [x] T045 Run all tests and verify 100% pass rate
- [x] T046 Run quickstart.md validation (manual or script)
- [x] T047 [P] Add py.typed marker for type checking in src/mcp_network_jcd/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P3)**: Can start after US1 (builds on single-command implementation)

### Within Each User Story (TDD Cycle)

1. Tests MUST be written first and FAIL (red phase)
2. Models before tool implementation
3. Tool implementation to pass tests (green phase)
4. Refactor if needed (refactor phase)

### Parallel Opportunities

Phase 1 (can run in parallel):
```
T003: Create __init__.py
T004: Create conftest.py
T005: Configure ruff
```

Phase 2 tests (can run in parallel):
```
T006: Test ServerCredentials
T007: Test DeviceConnection
T008: Test QueryRequest
```

Phase 2 models (can run in parallel):
```
T009: ServerCredentials model
T010: DeviceConnection model
T011: QueryRequest model
```

US1 tests (can run in parallel):
```
T015: Test CommandResult
T016: Test QueryResponse
T017: Contract test success
T018: Integration test SSH
```

US2 tests (can run in parallel):
```
T025: Test ErrorInfo
T026-T029: Error contract tests
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently with real device
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Single command queries work (MVP!)
3. Add User Story 2 → Error handling complete
4. Add User Story 3 → Batch queries work
5. Polish → Production ready

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [USn] label maps task to specific user story
- TDD mandatory per Constitution Principle II
- Verify tests fail before implementing (red phase)
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
