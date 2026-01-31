"""Setup module for configuring MCP servers in AI agent configurations.

This package provides automated configuration of MCP servers for various
AI coding agents. It supports workspace-level configuration (recommended)
to enable per-project civyk-repoix integration.

Supported Agents (MCP + Instruction Files):
    - Claude Code: .mcp.json + CLAUDE.md
    - Cursor: .cursor/mcp.json + .cursorrules
    - Windsurf: .windsurf/mcp.json + .windsurfrules
    - GitHub Copilot: .vscode/mcp.json + .github/copilot-instructions.md
    - OpenCode: .opencode/mcp.json + .opencode/instructions.md
    - Kilo Code: .kilo/mcp.json + .kilo/rules.md
    - Antigravity: .antigravity/mcp.json + .antigravity/instructions.md

Functions:
    setup_mcp: Configure MCP, instruction files, and .gitignore for agents
    configure_agent: Configure MCP for a specific agent
    configure_instruction_file: Configure instruction file for a specific agent
    configure_gitignore: Add required entries to .gitignore
    list_agents: List available agents and their MCP support status

Data:
    AGENT_CONFIG: Registry of supported agents with configuration paths
    AgentConfig: Configuration details for each agent

Usage:
    # Configure all supported agents (MCP + instructions + .gitignore)
    from civyk_repoix.setup import setup_mcp
    mcp_results, inst_results, gitignore_result = setup_mcp(Path.cwd())

    # Configure specific agent
    from civyk_repoix.setup import configure_agent, configure_instruction_file
    mcp_result = configure_agent("claude", Path.cwd())
    inst_result = configure_instruction_file("claude", Path.cwd())
"""

from civyk_repoix.setup.config import (
    AGENT_CONFIG,
    AgentConfig,
    get_agent_config,
    get_civyk_instruction_content,
    get_instruction_file_path,
    get_mcp_server_entry,
    get_vscode_mcp_server_entry,
    get_workspace_config_path,
)
from civyk_repoix.setup.mcp_setup import (
    GitignoreResult,
    InstructionResult,
    SetupResult,
    configure_agent,
    configure_gitignore,
    configure_instruction_file,
    list_agents,
    print_setup_results,
    setup_mcp,
)

__all__ = [
    "AGENT_CONFIG",
    "AgentConfig",
    "GitignoreResult",
    "InstructionResult",
    "SetupResult",
    "configure_agent",
    "configure_gitignore",
    "configure_instruction_file",
    "get_agent_config",
    "get_civyk_instruction_content",
    "get_instruction_file_path",
    "get_mcp_server_entry",
    "get_vscode_mcp_server_entry",
    "get_workspace_config_path",
    "list_agents",
    "print_setup_results",
    "setup_mcp",
]
