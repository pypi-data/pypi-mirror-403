"""
APE CLI Module v1.0.1

Agent Policy Engine
Version v1.0.1
https://github.com/kahalewai/agent-policy-engine

Command-line interface for APE operations.

Commands:
    Policy Commands:
        validate        Validate a policy file
        simulate        Test action against policy
        simulate-batch  Test multiple actions
        info            Show policy information
        diff            Compare two policies
    
    MCP Commands:
        mcp-scan        Generate policy from MCP config
        mcp-info        Show MCP config information
    
    v1.0.1 Commands:
        test-prompt     Test prompt through full pipeline
        analyze         Analyze prompt signals
        actions         List Action Repository
        generate-mocks  Generate mock tools for testing

Usage:
    ape --help
    ape <command> --help
"""

from ape.cli.main import main

__all__ = ["main"]
