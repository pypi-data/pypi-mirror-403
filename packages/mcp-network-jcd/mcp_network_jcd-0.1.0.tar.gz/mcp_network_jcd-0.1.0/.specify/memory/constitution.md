<!--
SYNC IMPACT REPORT
==================
Version change: N/A → 1.0.0 (initial ratification)
Modified principles: N/A (new constitution)
Added sections:
  - Core Principles (3 principles)
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ compatible (Constitution Check section exists)
  - .specify/templates/spec-template.md: ✅ compatible (user stories align with TDD)
  - .specify/templates/tasks-template.md: ✅ compatible (test-first workflow supported)
Follow-up TODOs: None
-->

# MCP Network JCD Constitution

## Core Principles

### I. MCP Protocol Compliance

All network monitoring and management functionality MUST be exposed through the Model Context
Protocol (MCP) interface. Tools MUST:

- Accept structured input via MCP tool parameters
- Return structured output (JSON) via MCP tool responses
- Report errors through proper MCP error responses with descriptive messages
- Be independently callable without requiring external state or session management

**Rationale**: MCP compliance ensures tools are composable, testable, and can be consumed by any
MCP-compatible client (Claude, other LLMs, automation scripts).

### II. Test-First Development (NON-NEGOTIABLE)

Test-Driven Development (TDD) is mandatory for all feature implementation:

1. Tests MUST be written before implementation code
2. Tests MUST fail initially (red phase) - this validates test correctness
3. Implementation MUST be minimal to pass tests (green phase)
4. Refactoring occurs only after tests pass (refactor phase)

**Enforcement**:
- Pull requests without corresponding tests for new functionality will be rejected
- Integration tests required for: MCP tool contracts, network protocol interactions
- Unit tests required for: data transformations, business logic, utility functions

**Rationale**: Test-first ensures features are specified before coded, reduces regressions, and
produces testable architecture by design.

### III. Simplicity

Start with the simplest solution that meets requirements. YAGNI (You Aren't Gonna Need It)
principles apply:

- No speculative features or "future-proofing" without documented requirements
- Prefer composition over inheritance
- Avoid abstractions until patterns repeat three or more times
- Configuration over code only when runtime flexibility is required

**Rationale**: Simpler code is easier to understand, test, maintain, and debug. Complexity MUST be
justified with specific requirements.

## Governance

This constitution supersedes all other development practices for the MCP Network JCD project.

**Amendment Process**:
1. Propose changes via pull request to `.specify/memory/constitution.md`
2. Changes require team review and explicit approval
3. Amendments MUST include migration guidance for in-flight work
4. Version increment follows semantic versioning (see below)

**Versioning Policy**:
- MAJOR: Principle removal, redefinition, or backward-incompatible governance changes
- MINOR: New principle/section added or material expansion of existing guidance
- PATCH: Clarifications, wording improvements, typo fixes

**Compliance Review**:
- All pull requests MUST verify compliance with constitution principles
- Constitution Check section in plan.md MUST be completed before implementation
- Violations require documented justification in Complexity Tracking section

**Version**: 1.0.0 | **Ratified**: 2026-01-30 | **Last Amended**: 2026-01-30
