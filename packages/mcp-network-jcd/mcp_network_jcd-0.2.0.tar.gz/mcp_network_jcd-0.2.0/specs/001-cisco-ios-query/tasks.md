# Tasks: Cisco IOS Query Tool

**Input**: Design documents from `/specs/001-cisco-ios-query/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Required (Constitution mandates Test-First Development)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## User Story Mapping

| Story | Title | Priority | Phase |
|-------|-------|----------|-------|
| US4 | Secure Credential Management | P1 | Phase 2 (Foundational) |
| US1 | Query Cisco IOS Device | P1 | Phase 3 (MVP) |
| US2 | Handle Connection Errors | P2 | Phase 4 |
| US3 | Execute Multiple Commands | P2 | Phase 5 |

---

## Phase 1: Setup

**Purpose**: Verify existing project structure supports new Cisco module

- [X] T001 Verify project structure matches plan.md layout in src/mcp_network_jcd/
- [X] T002 [P] Create empty src/mcp_network_jcd/models/cisco.py with module docstring
- [X] T003 [P] Create empty src/mcp_network_jcd/tools/cisco.py with module docstring
- [X] T004 [P] Create empty tests/unit/test_cisco_models.py with imports
- [X] T005 [P] Create empty tests/contract/test_cisco_tool.py with imports
- [X] T006 [P] Create empty tests/integration/test_cisco_ssh.py with imports

---

## Phase 2: Foundational - CiscoCredentials Model (US4)

**Purpose**: Core credential model that MUST be complete before any query functionality

**⚠️ CRITICAL**: US1 cannot work without this phase complete

**Goal**: Secure credential loading from environment variables

**Independent Test**: Run `pytest tests/unit/test_cisco_models.py` - all credential validation tests pass

### Tests for US4 (TDD - Write First, Must FAIL)

- [X] T007 [P] [US4] Write test_credentials_from_env_success in tests/unit/test_cisco_models.py
- [X] T008 [P] [US4] Write test_credentials_missing_username_raises in tests/unit/test_cisco_models.py
- [X] T009 [P] [US4] Write test_credentials_missing_password_raises in tests/unit/test_cisco_models.py
- [X] T010 [P] [US4] Write test_enable_password_optional in tests/unit/test_cisco_models.py
- [X] T011 [P] [US4] Write test_enable_password_empty_string_treated_as_none in tests/unit/test_cisco_models.py
- [X] T012 [US4] Verify all US4 tests FAIL (no implementation yet)

### Implementation for US4

- [X] T013 [US4] Implement CiscoCredentials model in src/mcp_network_jcd/models/cisco.py per data-model.md
- [X] T014 [US4] Run pytest tests/unit/test_cisco_models.py - all tests must PASS

**Checkpoint**: CiscoCredentials model complete - US1 can now proceed ✅

---

## Phase 3: User Story 1 - Query Cisco IOS Device (Priority: P1) 🎯 MVP

**Goal**: Execute read-only commands on Cisco IOS devices via SSH

**Independent Test**: Run `pytest tests/contract/test_cisco_tool.py tests/integration/test_cisco_ssh.py` - query functionality works

### Tests for US1 (TDD - Write First, Must FAIL)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Write test_returns_success_response_structure in tests/contract/test_cisco_tool.py
- [X] T016 [P] [US1] Write test_response_includes_device_info in tests/contract/test_cisco_tool.py
- [X] T017 [P] [US1] Write test_response_includes_results_array in tests/contract/test_cisco_tool.py
- [X] T018 [P] [US1] Write test_response_includes_timestamp in tests/contract/test_cisco_tool.py
- [X] T019 [P] [US1] Write test_single_command_execution in tests/integration/test_cisco_ssh.py
- [X] T020 [P] [US1] Write test_command_output_returned_unmodified in tests/integration/test_cisco_ssh.py
- [X] T021 [P] [US1] Write test_uses_cisco_ios_device_type in tests/integration/test_cisco_ssh.py
- [X] T022 [US1] Verify all US1 tests FAIL (no implementation yet)

### Implementation for US1

- [X] T023 [US1] Implement _create_error_response helper in src/mcp_network_jcd/tools/cisco.py
- [X] T024 [US1] Implement cisco_ios_query function in src/mcp_network_jcd/tools/cisco.py per contracts/cisco_ios_query.md
- [X] T025 [US1] Add cisco_ios_query_tool registration in src/mcp_network_jcd/server.py
- [X] T026 [US1] Run pytest tests/contract/test_cisco_tool.py tests/integration/test_cisco_ssh.py - all tests must PASS

**Checkpoint**: User Story 1 complete - basic query functionality works independently ✅

---

## Phase 4: User Story 2 - Handle Connection Errors (Priority: P2)

**Goal**: Clear error messages with appropriate error codes for all failure scenarios

**Independent Test**: Run `pytest tests/contract/test_cisco_tool.py -k error` - all error handling tests pass

### Tests for US2 (TDD - Write First, Must FAIL)

- [X] T027 [P] [US2] Write test_config_error_on_missing_credentials in tests/contract/test_cisco_tool.py
- [X] T028 [P] [US2] Write test_auth_failed_on_invalid_credentials in tests/integration/test_cisco_ssh.py
- [X] T029 [P] [US2] Write test_connection_timeout_on_unreachable_host in tests/integration/test_cisco_ssh.py
- [X] T030 [P] [US2] Write test_connection_refused_on_ssh_rejection in tests/integration/test_cisco_ssh.py
- [X] T031 [P] [US2] Write test_unknown_error_on_unexpected_exception in tests/integration/test_cisco_ssh.py
- [X] T032 [P] [US2] Write test_enable_auth_failed_on_wrong_enable_password in tests/integration/test_cisco_ssh.py
- [X] T033 [US2] Verify new US2 tests FAIL (need error handling implementation)

### Implementation for US2

- [X] T034 [US2] Add NetMikoAuthenticationException handling in src/mcp_network_jcd/tools/cisco.py
- [X] T035 [US2] Add NetMikoTimeoutException handling in src/mcp_network_jcd/tools/cisco.py
- [X] T036 [US2] Add SSHException handling in src/mcp_network_jcd/tools/cisco.py
- [X] T037 [US2] Add generic Exception handling in src/mcp_network_jcd/tools/cisco.py
- [X] T038 [US2] Run pytest tests/ -k "error or timeout or auth" - all error tests must PASS

**Checkpoint**: User Story 2 complete - all error scenarios handled with appropriate codes ✅

---

## Phase 5: User Story 3 - Execute Multiple Commands (Priority: P2)

**Goal**: Batch command execution with individual results and partial failure handling

**Independent Test**: Run `pytest tests/integration/test_cisco_ssh.py -k "multiple or batch or partial"` - batch tests pass

### Tests for US3 (TDD - Write First, Must FAIL)

- [X] T039 [P] [US3] Write test_multiple_commands_return_individual_results in tests/integration/test_cisco_ssh.py
- [X] T040 [P] [US3] Write test_each_command_has_duration_ms in tests/integration/test_cisco_ssh.py
- [X] T041 [P] [US3] Write test_partial_failure_returns_completed_results in tests/integration/test_cisco_ssh.py
- [X] T042 [P] [US3] Write test_batch_stops_on_connection_drop in tests/integration/test_cisco_ssh.py
- [X] T043 [US3] Verify new US3 tests FAIL (need batch implementation)

### Implementation for US3

- [X] T044 [US3] Implement command loop with individual timing in src/mcp_network_jcd/tools/cisco.py
- [X] T045 [US3] Add partial failure handling (OSError, TimeoutError) in src/mcp_network_jcd/tools/cisco.py
- [X] T046 [US3] Run pytest tests/integration/test_cisco_ssh.py -k "multiple or batch or partial" - all tests must PASS

**Checkpoint**: User Story 3 complete - batch execution with partial failure handling works ✅

---

## Phase 6: User Story 4 Enhancement - Enable Password Support

**Goal**: Support optional CISCO_ENABLE_PASSWORD for privileged mode access

**Independent Test**: Run `pytest tests/integration/test_cisco_ssh.py -k enable` - enable mode tests pass

### Tests for US4 Enhancement (TDD)

- [X] T047 [P] [US4] Write test_enable_mode_called_when_password_set in tests/integration/test_cisco_ssh.py
- [X] T048 [P] [US4] Write test_enable_mode_not_called_when_no_password in tests/integration/test_cisco_ssh.py
- [X] T049 [US4] Verify enable mode tests FAIL (need enable implementation)

### Implementation for US4 Enhancement

- [X] T050 [US4] Add enable password to ConnectHandler secret parameter in src/mcp_network_jcd/tools/cisco.py
- [X] T051 [US4] Call connection.enable() if enable_password is set in src/mcp_network_jcd/tools/cisco.py
- [X] T052 [US4] Run pytest tests/integration/test_cisco_ssh.py -k enable - all tests must PASS

**Checkpoint**: Enable password support complete - privileged mode access works ✅

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup

- [X] T053 Run ruff check src/mcp_network_jcd/models/cisco.py src/mcp_network_jcd/tools/cisco.py
- [X] T054 Run ruff check tests/unit/test_cisco_models.py tests/contract/test_cisco_tool.py tests/integration/test_cisco_ssh.py
- [X] T055 [P] Fix any linting issues found
- [X] T056 Run full test suite: pytest tests/ -k cisco
- [X] T057 Run quickstart.md validation commands
- [X] T058 Verify all success criteria from spec.md are met

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ✅
    ↓
Phase 2: Foundational (US4 - CiscoCredentials) ✅
    ↓
Phase 3: US1 - Query (P1 MVP) ✅
    ↓
Phase 4: US2 - Errors (P2) ✅

Phase 5: US3 - Batch (P2) ✅
    ↓
Phase 6: US4 Enhancement - Enable Password ✅
    ↓
Phase 7: Polish ✅
```

### User Story Dependencies

| Story | Depends On | Can Start After |
|-------|------------|-----------------|
| US4 (Foundational) | Setup | Phase 1 complete |
| US1 | US4 | Phase 2 complete |
| US2 | US1 | Phase 3 complete |
| US3 | US1 | Phase 3 complete |
| US4 Enhancement | US1 | Phase 3 complete |

### Within Each User Story

1. Tests MUST be written FIRST and FAIL
2. Implementation makes tests PASS
3. Checkpoint verification before next phase

### Parallel Opportunities

**Setup (Phase 1):**
```
T002, T003, T004, T005, T006 can run in parallel
```

**US4 Tests (Phase 2):**
```
T007, T008, T009, T010, T011 can run in parallel
```

**US1 Tests (Phase 3):**
```
T015, T016, T017, T018, T019, T020, T021 can run in parallel
```

**US2 Tests (Phase 4):**
```
T027, T028, T029, T030, T031, T032 can run in parallel
```

**US3 Tests (Phase 5):**
```
T039, T040, T041, T042 can run in parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CiscoCredentials)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `pytest tests/ -k cisco` should pass basic tests
5. Tool is functional for single command queries

### Incremental Delivery

1. Setup + Foundational → CiscoCredentials working
2. Add US1 → Basic query works → **MVP!**
3. Add US2 → Error handling complete
4. Add US3 → Batch execution works
5. Add US4 Enhancement → Enable password support
6. Polish → Production ready

### File Creation Summary

| File | Phase | Story |
|------|-------|-------|
| src/mcp_network_jcd/models/cisco.py | 1, 2 | US4 |
| src/mcp_network_jcd/tools/cisco.py | 1, 3-6 | US1, US2, US3, US4 |
| src/mcp_network_jcd/server.py | 3 | US1 |
| tests/unit/test_cisco_models.py | 1, 2 | US4 |
| tests/contract/test_cisco_tool.py | 1, 3, 4 | US1, US2 |
| tests/integration/test_cisco_ssh.py | 1, 3-6 | US1, US2, US3, US4 |

---

## Notes

- [P] tasks = different files, no dependencies within same phase
- [Story] label maps task to specific user story for traceability
- Constitution mandates TDD: tests MUST fail before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Run `pytest tests/ -k cisco` frequently to verify progress
