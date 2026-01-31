# Research: Cisco IOS Query Tool

**Feature**: 001-cisco-ios-query
**Date**: 2026-01-30

## Research Topics

### 1. Netmiko Device Type for Cisco IOS

**Decision**: Use `cisco_ios` device type

**Rationale**:
- netmiko provides `cisco_ios` for standard Cisco IOS and IOS-XE devices
- Handles standard prompts (`hostname>`, `hostname#`)
- Supports `enable` command for privilege escalation
- Well-tested and stable in production environments

**Alternatives Considered**:
- `cisco_ios_telnet`: Rejected - Telnet is insecure and out of scope
- `cisco_xe`: Considered but `cisco_ios` works for both IOS and IOS-XE
- `autodetect`: Rejected - adds latency and complexity; we know the target platform

### 2. Enable Password Handling

**Decision**: Use netmiko's `secret` parameter with `enable()` method

**Rationale**:
- netmiko `ConnectHandler` accepts `secret` parameter for enable password
- Call `connection.enable()` after connection if enable password is provided
- This matches standard Cisco privilege escalation workflow
- If no enable password provided, assume user lands in privileged mode (privilege 15)

**Implementation Pattern**:
```python
connection = ConnectHandler(
    device_type="cisco_ios",
    host=host,
    username=credentials.username,
    password=credentials.password,
    secret=credentials.enable_password,  # Optional
    timeout=timeout,
)
if credentials.enable_password:
    connection.enable()  # Sends "enable" + secret
```

**Alternatives Considered**:
- Manual `send_command("enable")` + password: Rejected - netmiko handles this better
- Always call `enable()`: Rejected - may fail if no enable password configured on device

### 3. Model Reuse Strategy

**Decision**: Create `CiscoCredentials` model; reuse `QueryResponse`, `CommandResult`, `DeviceInfo`, `ErrorInfo`

**Rationale**:
- `CiscoCredentials` needs different env vars (CISCO_*) and optional `enable_password` field
- Response structure is identical to Palo Alto - same JSON contract for Claude Desktop consistency
- Avoids code duplication while allowing vendor-specific credential handling

**Alternatives Considered**:
- Full model duplication: Rejected - violates DRY, maintenance burden
- Generic `NetworkCredentials` base class: Rejected - premature abstraction (only 2 vendors)
- Single credentials model with vendor flag: Rejected - env var handling differs

### 4. Error Code Mapping

**Decision**: Reuse same error codes as Palo Alto tool

| Error Code | Cisco Scenario |
|------------|----------------|
| CONFIG_ERROR | CISCO_USERNAME or CISCO_PASSWORD not set |
| AUTH_FAILED | SSH auth failed OR enable password rejected |
| CONNECTION_TIMEOUT | Device unreachable within timeout |
| CONNECTION_REFUSED | SSH port closed or filtered |
| UNKNOWN_ERROR | Unexpected exceptions |

**Rationale**:
- Consistent error handling across tools
- Claude Desktop can handle errors uniformly
- Maps to same netmiko exceptions (NetMikoAuthenticationException, NetMikoTimeoutException)

### 5. Enable Mode Detection

**Decision**: Check prompt after `enable()` to confirm privileged mode

**Rationale**:
- After `enable()`, prompt should change from `>` to `#`
- If enable fails, netmiko raises exception which we catch as AUTH_FAILED
- No need for explicit prompt detection - netmiko handles internally

**Alternatives Considered**:
- Parse prompt manually: Rejected - netmiko already does this
- Send test command to verify mode: Rejected - adds latency, unnecessary

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| netmiko | >=4.0.0 | SSH connectivity, device type handling, enable mode |
| pydantic | >=2.0.0 | Model validation, serialization |
| mcp | >=1.0.0 | FastMCP tool registration |

No new dependencies required. Existing stack fully supports Cisco IOS connectivity.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Non-standard prompts | Low | Medium | Document supported prompt formats; timeouts catch edge cases |
| Enable password complexity | Low | Low | netmiko handles various enable scenarios |
| Command output size | Medium | Low | Document recommendation to use filtered commands |

## Conclusion

All technical decisions align with existing patterns. No blockers identified. Ready for Phase 1 design.
