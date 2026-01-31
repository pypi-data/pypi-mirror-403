#!/usr/bin/env python3
"""
Validation script for MCP implementation.

Checks structure, imports, and schemas without requiring mcp package.
"""

import sys
from pathlib import Path


def validate_structure():
    """Validate file structure."""
    print("=== Validating File Structure ===")

    mcp_dir = Path(__file__).parent
    required_files = [
        "__init__.py",
        "tools.py",
        "handlers.py",
        "server.py",
        "example.py",
        "README.md",
        "IMPLEMENTATION.md",
    ]

    for filename in required_files:
        filepath = mcp_dir / filename
        if filepath.exists():
            print(f"✓ {filename} exists ({filepath.stat().st_size} bytes)")
        else:
            print(f"✗ {filename} MISSING")
            return False

    return True


def validate_tools():
    """Validate tool definitions."""
    print("\n=== Validating Tool Definitions ===")

    try:
        from .tools import CORE_TOOLS, EXTENDED_TOOLS

        # Check core tools
        assert len(CORE_TOOLS) == 6, f"Expected 6 core tools, got {len(CORE_TOOLS)}"
        print(f"✓ Core tools: {len(CORE_TOOLS)}")

        core_tool_names = [
            "memory_remember",
            "memory_recall",
            "memory_reflect",
            "memory_forget",
            "memory_associate",
            "memory_briefing",
        ]

        actual_core_names = [tool["name"] for tool in CORE_TOOLS]
        for name in core_tool_names:
            if name in actual_core_names:
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name} MISSING")
                return False

        # Check extended tools
        assert len(EXTENDED_TOOLS) == 4, f"Expected 4 extended tools, got {len(EXTENDED_TOOLS)}"
        print(f"\n✓ Extended tools: {len(EXTENDED_TOOLS)}")

        extended_tool_names = [
            "memory_statistics",
            "memory_graph_query",
            "memory_audit",
            "memory_compress",
        ]

        actual_extended_names = [tool["name"] for tool in EXTENDED_TOOLS]
        for name in extended_tool_names:
            if name in actual_extended_names:
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name} MISSING")
                return False

        # Validate schemas
        print("\n✓ Validating tool schemas...")
        for tool in CORE_TOOLS + EXTENDED_TOOLS:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool missing 'description': {tool}"
            assert "inputSchema" in tool, f"Tool missing 'inputSchema': {tool}"
            assert tool["inputSchema"]["type"] == "object", f"Invalid schema type for {tool['name']}"
            print(f"  ✓ {tool['name']} schema valid")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"✗ Assertion error: {e}")
        return False


def validate_handlers():
    """Validate handler implementations."""
    print("\n=== Validating Handler Implementations ===")

    try:
        from .handlers import MCPToolHandlers

        # Check handler methods exist
        handler_methods = [
            "handle_memory_remember",
            "handle_memory_recall",
            "handle_memory_reflect",
            "handle_memory_forget",
            "handle_memory_associate",
            "handle_memory_briefing",
            "handle_memory_statistics",
            "handle_memory_graph_query",
            "handle_memory_audit",
            "handle_memory_compress",
        ]

        for method_name in handler_methods:
            if hasattr(MCPToolHandlers, method_name):
                print(f"✓ {method_name}")
            else:
                print(f"✗ {method_name} MISSING")
                return False

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  This is expected if dependencies are not installed")
        return False


def validate_pyproject():
    """Validate pyproject.toml has mcp dependency."""
    print("\n=== Validating pyproject.toml ===")

    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"✗ pyproject.toml not found at {pyproject_path}")
        return False

    content = pyproject_path.read_text()

    if 'mcp>=' in content:
        print("✓ mcp dependency found in pyproject.toml")
        return True
    else:
        print("✗ mcp dependency NOT found in pyproject.toml")
        return False


def main():
    """Run all validations."""
    print("MCP Implementation Validation")
    print("=" * 50)

    results = []

    results.append(("File Structure", validate_structure()))
    results.append(("Tool Definitions", validate_tools()))
    results.append(("Handler Implementations", validate_handlers()))
    results.append(("pyproject.toml", validate_pyproject()))

    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)

    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {name}: {status}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
        print("\nNext steps:")
        print("1. Install mcp package: pip install mcp")
        print("2. Install memorylayer: pip install -e .")
        print("3. Run example: python -m memorylayer_server.mcp.example")
        return 0
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("\nPlease fix the failures above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
