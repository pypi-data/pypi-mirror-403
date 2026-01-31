# Feature Specification: Cisco IOS Query Tool

**Feature Branch**: `001-cisco-ios-query`
**Created**: 2026-01-30
**Status**: Draft
**Input**: User description: "On va ajouter un outil 'cisco_ios_query' au MCP server"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Cisco IOS Device (Priority: P1)

As a network administrator using Claude Desktop, I want to query Cisco IOS devices (routers, switches) via the MCP server so that I can retrieve configuration and status information without leaving my AI assistant interface.

**Why this priority**: This is the core functionality of the tool. Without the ability to execute read-only commands on Cisco IOS devices, the tool has no value.

**Independent Test**: Can be fully tested by connecting to a Cisco IOS device and executing a single "show version" command, which delivers immediate value by returning device information.

**Acceptance Scenarios**:

1. **Given** a reachable Cisco IOS device with valid credentials, **When** I execute the command "show version", **Then** I receive the device version information with success status.
2. **Given** valid credentials and a list of commands ["show ip interface brief", "show running-config | section hostname"], **When** I execute the query, **Then** I receive structured results for each command with output and timing.
3. **Given** a command that produces output, **When** the command is executed, **Then** the output is returned as a string without modification.

---

### User Story 2 - Handle Connection Errors (Priority: P2)

As a network administrator, I want clear error messages when connection issues occur so that I can diagnose and resolve problems quickly.

**Why this priority**: Error handling is essential for production use. Users need actionable feedback when things go wrong.

**Independent Test**: Can be tested by intentionally providing invalid credentials or unreachable hosts and verifying the error response structure and messages.

**Acceptance Scenarios**:

1. **Given** invalid credentials, **When** I attempt to query a device, **Then** I receive an authentication failed error with code "AUTH_FAILED".
2. **Given** an unreachable host, **When** I attempt to query, **Then** I receive a timeout error with code "CONNECTION_TIMEOUT" after the configured timeout period.
3. **Given** a host that refuses SSH connections, **When** I attempt to query, **Then** I receive a connection refused error with code "CONNECTION_REFUSED".
4. **Given** missing environment credentials, **When** I attempt to query, **Then** I receive a configuration error with code "CONFIG_ERROR" indicating which credentials are missing.

---

### User Story 3 - Execute Multiple Commands (Priority: P2)

As a network administrator, I want to execute multiple commands in a single query to efficiently gather related information from a device.

**Why this priority**: Batch command execution reduces round-trips and improves efficiency for common workflows like auditing or troubleshooting.

**Independent Test**: Can be tested by sending multiple commands (e.g., ["show version", "show ip route", "show interfaces status"]) and verifying each command result is returned with individual timing and status.

**Acceptance Scenarios**:

1. **Given** a list of 3 valid commands, **When** I execute the query, **Then** I receive 3 separate results with individual success status, output, and duration.
2. **Given** a list of commands where the 2nd command fails (e.g., connection drops), **When** executed, **Then** I receive results for completed commands, an error for the failed command, and the batch stops execution at failure point.

---

### User Story 4 - Secure Credential Management (Priority: P1)

As a security-conscious administrator, I want credentials to be managed securely via environment variables so that they are never exposed in tool parameters or logs.

**Why this priority**: Security is non-negotiable. Credentials must never appear in API calls, logs, or error messages.

**Independent Test**: Can be verified by inspecting tool parameter schema (no credential fields) and checking that credentials only come from CISCO_USERNAME, CISCO_PASSWORD, and optionally CISCO_ENABLE_PASSWORD environment variables.

**Acceptance Scenarios**:

1. **Given** CISCO_USERNAME and CISCO_PASSWORD are set in the environment, **When** I call the tool, **Then** no credentials are required or accepted as parameters.
2. **Given** credentials are loaded from environment, **When** an error occurs, **Then** the error message does not reveal credentials or usernames.
3. **Given** CISCO_ENABLE_PASSWORD is set in the environment, **When** I connect to a device requiring enable authentication, **Then** the tool automatically enters privileged EXEC mode using the enable password.

---

### Edge Cases

- What happens when the command list is empty? → Tool rejects with validation error.
- What happens when the command list exceeds 10 commands? → Tool rejects with validation error.
- What happens when a command produces very large output? → Output is returned but may exceed practical processing limits; users should use filtered commands.
- What happens when the device prompt is non-standard? → The tool handles standard Cisco IOS prompts; non-standard prompts may cause timeouts.
- What happens when the SSH connection drops mid-batch? → Partial results are returned with an error for the failed command.
- What happens when CISCO_ENABLE_PASSWORD is set but incorrect? → Tool returns AUTH_FAILED error indicating enable authentication failed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `cisco_ios_query` tool accessible via the MCP server.
- **FR-002**: System MUST accept host (required), commands (required, 1-10 items), port (optional, default 22), and timeout (optional, default 30 seconds) as parameters.
- **FR-003**: System MUST load credentials from environment variables CISCO_USERNAME and CISCO_PASSWORD.
- **FR-003a**: System SHOULD support optional CISCO_ENABLE_PASSWORD environment variable; if set, system sends "enable" command after SSH login to enter privileged EXEC mode.
- **FR-004**: System MUST NOT accept credentials as tool parameters.
- **FR-005**: System MUST execute commands sequentially on the target Cisco IOS device via SSH.
- **FR-006**: System MUST return structured responses including: success status, device info (host, port), command results array, total duration, and timestamp.
- **FR-007**: Each command result MUST include: command string, success status, output (on success), error message (on failure), and individual duration.
- **FR-008**: System MUST return appropriate error codes: CONFIG_ERROR (missing credentials), AUTH_FAILED (invalid credentials), CONNECTION_TIMEOUT (device unreachable), CONNECTION_REFUSED (SSH refused), UNKNOWN_ERROR (unexpected errors).
- **FR-009**: System MUST validate input parameters: host non-empty, port 1-65535, timeout 1-300 seconds, commands 1-10 items with non-empty strings.
- **FR-010**: System MUST handle partial failures by returning completed results when connection drops mid-batch.

### Key Entities

- **Query Request**: Encapsulates host, port, commands list, and timeout for a single device query.
- **Query Response**: Contains success status, device info, optional results array, optional error info, total duration, and timestamp.
- **Command Result**: Individual command outcome with command string, success status, output or error, and duration.
- **Error Info**: Connection-level error with code and human-readable message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can execute read-only commands on Cisco IOS devices directly from Claude Desktop.
- **SC-002**: Single command queries complete within the configured timeout period (default 30 seconds).
- **SC-003**: Batch queries of up to 10 commands complete successfully with individual timing for each command.
- **SC-004**: 100% of connection failures return structured error responses with appropriate error codes.
- **SC-005**: Credentials are never exposed in tool parameters, API responses, or error messages.
- **SC-006**: The tool follows the same interaction patterns as the existing Palo Alto query tool, ensuring consistent user experience.

## Clarifications

### Session 2026-01-30

- Q: How should the tool handle Cisco privilege levels? → A: Support optional CISCO_ENABLE_PASSWORD env var; send "enable" command if set.

## Assumptions

- Cisco IOS devices support standard SSH access on the configured port.
- Environment variables CISCO_USERNAME and CISCO_PASSWORD will be configured by the server administrator.
- Optional environment variable CISCO_ENABLE_PASSWORD may be configured; if set, the tool sends "enable" command after login to enter privileged EXEC mode.
- Commands are read-only show/diagnostic commands; configuration changes are out of scope.
- The tool targets standard Cisco IOS and IOS-XE platforms; other platforms (NX-OS, IOS-XR) are out of scope for this feature.
- Standard Cisco IOS CLI prompts are used (e.g., `hostname#` or `hostname>`).
