"""
AI Security MCP - Cloud-Powered Agentic Security Scanner

Thin client proxy that connects Claude Code to cloud-hosted comprehensive
agentic AI security scanner with 27 specialized agents covering 100% OWASP
ASI (Agentic Security Interface) and LLM vulnerabilities.

Architecture:
    This package is a lightweight HTTP proxy (~50KB) that forwards MCP requests
    from Claude Code to our secure cloud infrastructure where all 27 security
    agents execute. No proprietary agent code is included in this package.

Features:
    - Connects to 27 cloud-hosted security agents (17 ASI + 10 LLM)
    - 100% OWASP ASI + LLM coverage via cloud processing
    - Secure API key authentication
    - Sub-second scan response times
    - Comprehensive vulnerability detection with remediation guidance
    - Native Claude Code integration via MCP protocol

Setup:
    1. Get API key from https://app.ai-threat-scanner.com/dashboard/api-keys
    2. Install with: claude mcp add ai-security-scanner \
                       -e AI_SECURITY_API_KEY=your_key_here \
                       -- uvx ai-security-mcp

Usage:
    After installation with your API key, simply ask Claude Code:

    "Scan this repository for agentic AI vulnerabilities"

    The thin client will connect to our cloud infrastructure, execute all 27
    security agents, and return comprehensive security findings.

Cloud Architecture:
    Your Machine              Cloud Infrastructure
    ┌─────────────┐          ┌──────────────────────┐
    │ Claude Code │─────────▶│ Cloud MCP Server     │
    │             │  HTTPS   │ - 27 Security Agents │
    │ Thin Client │◀─────────│ - Analysis Engine    │
    │ (this pkg)  │          │ - Quota Tracking     │
    └─────────────┘          └──────────────────────┘
"""

__version__ = "1.0.31"
__author__ = "AI Security Team"
__email__ = "security@ai-threat-scanner.com"
__license__ = "MIT"

# Package exports - thin client only exports main
from .main import main

__all__ = ["main", "__version__"]