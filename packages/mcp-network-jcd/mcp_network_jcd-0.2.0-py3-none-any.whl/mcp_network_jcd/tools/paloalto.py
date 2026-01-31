"""Palo Alto query tool implementation."""

import time

import netmiko
from netmiko.exceptions import NetMikoAuthenticationException, NetMikoTimeoutException
from paramiko.ssh_exception import SSHException

from mcp_network_jcd.models.paloalto import (
    CommandResult,
    DeviceInfo,
    ErrorInfo,
    QueryResponse,
    ServerCredentials,
)


def _create_error_response(
    host: str,
    port: int,
    code: str,
    message: str,
    start_time: float,
) -> dict:
    """Create error response dictionary."""
    total_duration = int((time.time() - start_time) * 1000)
    response = QueryResponse(
        success=False,
        device=DeviceInfo(host=host, port=port),
        error=ErrorInfo(code=code, message=message),
        total_duration_ms=total_duration,
    )
    return response.model_dump()


def paloalto_query(
    host: str,
    commands: list[str],
    port: int = 22,
    timeout: int = 30,
) -> dict:
    """
    Query a Palo Alto firewall via SSH.

    Executes one or more read-only commands and returns structured results.
    Credentials are read from environment variables (PALOALTO_USERNAME, PALOALTO_PASSWORD).

    IMPORTANT: Avoid commands that generate large outputs (several MB) as they cannot be
    processed. Use filtered or specific commands instead of broad ones.

    Args:
        host: Device hostname or IP address
        commands: List of PAN-OS CLI commands to execute (1-10 commands)
        port: SSH port (default: 22)
        timeout: Connection timeout in seconds (default: 30)

    Returns:
        dict: Structured response with command results
    """
    start_time = time.time()

    try:
        credentials = ServerCredentials.from_env()
    except ValueError as e:
        return _create_error_response(
            host=host,
            port=port,
            code="CONFIG_ERROR",
            message=f"PALOALTO_USERNAME and PALOALTO_PASSWORD must be set: {e}",
            start_time=start_time,
        )

    device_info = DeviceInfo(host=host, port=port)

    try:
        connection = netmiko.ConnectHandler(
            device_type="paloalto_panos",
            host=host,
            port=port,
            username=credentials.username,
            password=credentials.password,
            timeout=timeout,
            ssh_strict=False,
        )
    except NetMikoAuthenticationException:
        return _create_error_response(
            host=host,
            port=port,
            code="AUTH_FAILED",
            message="Authentication failed: invalid credentials",
            start_time=start_time,
        )
    except NetMikoTimeoutException:
        return _create_error_response(
            host=host,
            port=port,
            code="CONNECTION_TIMEOUT",
            message=f"Device unreachable: connection timed out after {timeout} seconds",
            start_time=start_time,
        )
    except SSHException:
        return _create_error_response(
            host=host,
            port=port,
            code="CONNECTION_REFUSED",
            message="SSH connection refused by device",
            start_time=start_time,
        )
    except Exception as e:
        return _create_error_response(
            host=host,
            port=port,
            code="UNKNOWN_ERROR",
            message=f"Unexpected error: {type(e).__name__}",
            start_time=start_time,
        )

    results = []
    try:
        for cmd in commands:
            cmd_start = time.time()
            try:
                output = connection.send_command(cmd)
                cmd_duration = int((time.time() - cmd_start) * 1000)

                results.append(
                    CommandResult(
                        command=cmd,
                        success=True,
                        output=output,
                        duration_ms=cmd_duration,
                    )
                )
            except (OSError, TimeoutError) as e:
                cmd_duration = int((time.time() - cmd_start) * 1000)
                results.append(
                    CommandResult(
                        command=cmd,
                        success=False,
                        error=f"Connection lost during command: {type(e).__name__}",
                        duration_ms=cmd_duration,
                    )
                )
                break
            except Exception as e:
                cmd_duration = int((time.time() - cmd_start) * 1000)
                results.append(
                    CommandResult(
                        command=cmd,
                        success=False,
                        error=f"Command failed: {type(e).__name__}: {e}",
                        duration_ms=cmd_duration,
                    )
                )
    finally:
        connection.disconnect()

    total_duration = int((time.time() - start_time) * 1000)

    response = QueryResponse(
        success=True,
        device=device_info,
        results=results,
        total_duration_ms=total_duration,
    )

    return response.model_dump()
