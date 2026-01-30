#!/usr/bin/env python3
"""
AI Security MCP Thin Client
Lightweight MCP server that proxies requests to cloud MCP server via HTTP
"""

import asyncio
import httpx
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging to stderr (stdio goes to stdout for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Cloud MCP server URL
CLOUD_MCP_URL = os.getenv(
    'AI_SECURITY_MCP_URL',
    'https://ciso-mcp-server-production.up.railway.app'
)

# User's API key from environment
API_KEY = os.getenv('AI_SECURITY_API_KEY')

# HTTP client for cloud API calls
http_client: Optional[httpx.AsyncClient] = None


class ScanResult(BaseModel):
    """Security scan result model"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def validate_environment():
    """Validate required environment variables"""
    if not API_KEY:
        logger.error("AI_SECURITY_API_KEY environment variable is required")
        print("\n" + "="*60, file=sys.stderr)
        print("ERROR: API Key Required", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print("\nThe AI Security MCP thin client requires an API key.", file=sys.stderr)
        print("\nSteps to get your API key:", file=sys.stderr)
        print("1. Visit: https://app.ai-threat-scanner.com/dashboard/api-keys", file=sys.stderr)
        print("2. Generate a new API key", file=sys.stderr)
        print("3. Set environment variable:", file=sys.stderr)
        print("   export AI_SECURITY_API_KEY=ciso_live_your_key_here", file=sys.stderr)
        print("\nOr configure in Claude Code:", file=sys.stderr)
        print("   Add to .claude/settings.json:", file=sys.stderr)
        print('   "env": {"AI_SECURITY_API_KEY": "ciso_live_your_key_here"}', file=sys.stderr)
        print("\n" + "="*60, file=sys.stderr)
        sys.exit(1)

    logger.info("Environment validation passed")
    logger.info(f"Using cloud MCP server: {CLOUD_MCP_URL}")
    logger.info(f"API key configured: {API_KEY[:15]}...")


# ========== Report File Generation Utilities ==========
# Copied from: saas_platform/mcp-fastmcp-service/cli-src/reporting/report_persistence.py
# Date: 2025-10-27
# Purpose: Enable client-side file generation for scan reports


def sanitize_repository_name(repository: str) -> str:
    """
    Sanitize repository name for filesystem paths.

    Removes path separators and invalid filesystem characters to prevent
    path traversal attacks and ensure cross-platform compatibility.

    Args:
        repository: Raw repository name or path

    Returns:
        Sanitized string safe for use in file paths

    Example:
        >>> sanitize_repository_name("/path/to/my-app/frontend")
        "path_to_my-app_frontend"
    """
    # Remove path separators
    name = repository.replace("/", "_").replace("\\", "_")

    # Remove invalid filesystem characters
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")

    # Remove leading/trailing whitespace and dots
    return name.strip().strip(".")


def get_report_filename(
    report_type: str,
    timestamp: datetime,
    scan_id: str
) -> str:
    """
    Generate filename with scan_id for uniqueness.

    Args:
        report_type: Type of report (agentic_security, comprehensive_analysis, coverage)
        timestamp: When the report was generated
        scan_id: Unique scan identifier from cloud server

    Returns:
        Filename string with format: {type}_YYYYMMDD_HHMMSS_{scan_id}.md

    Example:
        >>> get_report_filename("agentic_security", datetime(2025, 10, 27, 14, 30), "scan_123")
        "AgenticSecurityReport_20251027_143000_scan123.md"
    """
    type_map = {
        "agentic_security": "AgenticSecurityReport",
        "comprehensive_analysis": "ComprehensiveAnalysis",
        "coverage": "CoverageReport",
    }

    date_str = timestamp.strftime("%Y%m%d")
    time_str = timestamp.strftime("%H%M%S")

    # Extract short identifier from scan_id
    # Handle formats: "fastmcp_scan_1730000000" or "abc123-def456-..."
    scan_id_parts = scan_id.replace("_", "-").split("-")
    scan_id_short = scan_id_parts[-1][:8]  # Last segment, first 8 chars

    filename = f"{type_map.get(report_type, report_type)}_{date_str}_{time_str}_{scan_id_short}"

    return f"{filename}.md"


async def save_reports_to_filesystem(
    scan_id: str,
    repository: str,
    reports: dict,
    base_directory: str = "AIThreatScannerReports"
) -> dict:
    """
    Save reports from cloud MCP response to local filesystem.

    Creates directory structure and saves all 3 report types with standardized
    filenames. Errors are non-fatal - function returns error details but does
    not raise exceptions.

    Args:
        scan_id: UUID from scan response
        repository: Repository path/name from scan request
        reports: Dict with keys: agentic_security, comprehensive_analysis, coverage
        base_directory: Root directory for all reports (default: AIThreatScannerReports)

    Returns:
        dict: {
            "success": bool,          # True if all reports saved successfully
            "directory": str,         # Absolute path to repo directory
            "saved_paths": list[str], # List of successfully saved file paths
            "errors": list[str]       # List of error messages (empty if success)
        }

    Example:
        >>> result = await save_reports_to_filesystem(
        ...     scan_id="scan_123",
        ...     repository="/path/to/my-app",
        ...     reports={"agentic_security": "# Report...", ...}
        ... )
        >>> result["success"]
        True
        >>> len(result["saved_paths"])
        3
    """
    try:
        # Sanitize repository name for filesystem
        repo_name = sanitize_repository_name(repository)

        # Create directory structure
        base_path = Path(base_directory)
        repo_path = base_path / repo_name
        repo_path.mkdir(parents=True, exist_ok=True)

        # Save each report type
        saved_paths = []
        errors = []
        timestamp = datetime.now()

        for report_type, content in reports.items():
            try:
                filename = get_report_filename(report_type, timestamp, scan_id)
                file_path = repo_path / filename

                # Synchronous write (fast, no async overhead needed)
                file_path.write_text(content, encoding='utf-8')

                saved_paths.append(str(file_path.absolute()))

            except Exception as e:
                error_msg = f"Failed to save {report_type}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        return {
            "success": len(saved_paths) == len(reports),
            "directory": str(repo_path.absolute()),
            "saved_paths": saved_paths,
            "errors": errors
        }

    except Exception as e:
        # Catastrophic error (e.g., base directory creation failed)
        error_msg = f"Failed to create report directory: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "directory": "",
            "saved_paths": [],
            "errors": [error_msg]
        }

# ========== End Report File Generation Utilities ==========


async def call_cloud_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call a tool on the cloud MCP server via HTTP

    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments

    Returns:
        Tool result from cloud server
    """
    global http_client

    if http_client is None:
        http_client = httpx.AsyncClient(timeout=60.0)

    try:
        # Call cloud MCP server's custom HTTP endpoint (no session required)
        response = await http_client.post(
            f"{CLOUD_MCP_URL}/api/tools/call",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
        )
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            raise Exception(f"Cloud MCP error: {result['error']}")

        # Parse JSON-RPC 2.0 wrapper from /api/tools/call endpoint
        # Actual response format: {jsonrpc, id, result: {result: {content: [{text: "..."}]}}}
        outer_result = result.get("result", {})

        # Parse FastMCP protocol wrapper inside JSON-RPC 'result' field
        try:
            # Extract result.result.content[0].text path (JSON-RPC → FastMCP → content → text)
            if "result" in outer_result and isinstance(outer_result["result"], dict):
                fastmcp_result = outer_result["result"]
                if "content" in fastmcp_result:
                    content = fastmcp_result.get("content", [])
                    if content and len(content) > 0 and "text" in content[0]:
                        # Parse the JSON string in the text field
                        result_text = content[0]["text"]
                        return json.loads(result_text)

            # Fallback: return original if not expected format
            return outer_result if outer_result else result
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse tool result JSON: {e}. Content: {result_text[:200]}")
        except Exception as e:
            raise ValueError(f"Unexpected response format from cloud server: {e}")

    except Exception as e:
        logger.error(f"Failed to call cloud tool {tool_name}: {e}")
        raise


# Initialize FastMCP server
mcp = FastMCP(
    "AI Security Scanner",
    version="1.0.31"
)


@mcp.tool()
async def scan_repository(
    path: str = Field(
        description="File or directory path to scan for security vulnerabilities"
    ),
    format: str = Field(
        default="detailed",
        description="Output format: 'detailed' or 'summary'"
    )
) -> ScanResult:
    """
    Scan repository or file path for AI security vulnerabilities.

    This tool analyzes code for security issues specific to AI/ML systems including:
    - Prompt injection vulnerabilities
    - Insecure deserialization of models
    - Unsafe model loading
    - Credential exposure in model artifacts
    - AI-specific input validation issues

    Args:
        path: File or directory path to scan
        format: Output format - 'detailed' for full report, 'summary' for overview

    Returns:
        ScanResult with vulnerability findings

    Example:
        scan_repository(path="/path/to/code", format="detailed")
    """
    try:
        logger.info(f"Scanning repository: {path}")

        # Call cloud MCP server
        result = await call_cloud_tool(
            "scan_repository",
            {"path": path, "format": format}
        )

        logger.info(f"Scan completed: {path}")

        # Save reports to filesystem if included in response
        if result.get("success") and "reports" in result:
            try:
                save_result = await save_reports_to_filesystem(
                    scan_id=result["scan_id"],
                    repository=path,
                    reports=result["reports"]
                )

                if save_result["success"]:
                    print(f"\nReports saved to: {Path('AIThreatScannerReports').absolute()}", file=sys.stderr)
                    for file_path in save_result["saved_paths"]:
                        print(f"   - {file_path}", file=sys.stderr)
                else:
                    print(f"\nSome reports failed to save:", file=sys.stderr)
                    for error in save_result["errors"]:
                        print(f"   - {error}", file=sys.stderr)

            except Exception as e:
                # Non-fatal: log warning but don't fail the scan
                logger.warning(f"Report file generation failed (non-fatal): {e}")
                print(f"\nCould not save report files: {e}", file=sys.stderr)
                print("   (Scan results are still available above)", file=sys.stderr)

        return ScanResult(
            success=True,
            data=result,
            metadata={"path": path, "format": format}
        )

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return ScanResult(
            success=False,
            error=str(e)
        )


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Check health status of the AI Security Scanner service.

    Returns service health information including:
    - Service status (healthy, degraded, unhealthy)
    - Database connectivity
    - Active API keys count
    - Service uptime

    Returns:
        Health status information

    Example:
        health_check()
    """
    try:
        logger.info("Performing health check")

        # Call cloud MCP server
        result = await call_cloud_tool("health_check", {})

        logger.info(f"Health check result: {result.get('status', 'unknown')}")

        return result

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def main():
    """Main entry point for the thin client"""
    logger.info("AI Security MCP Thin Client starting...")

    # Validate environment
    validate_environment()

    try:
        # Run FastMCP server over stdio
        logger.info("Starting MCP server over stdio...")
        mcp.run(transport="stdio")

    except KeyboardInterrupt:
        logger.info("Thin client stopped by user")
    except Exception as e:
        logger.error(f"Thin client failed: {str(e)}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        # Cleanup
        if http_client:
            asyncio.run(http_client.aclose())
        logger.info("AI Security MCP Thin Client terminated")


if __name__ == "__main__":
    main()
