"""Unit tests for tool registry operations.

These tests verify that the tool registry correctly manages tools
and provides access to tool implementations.
"""

import pytest


class TestToolRegistry:
    """Tests for tool registry operations."""

    def test_tool_registry_operations(self) -> None:
        """Test basic tool registry operations.

        Verifies:
        - get_available_tools() returns list
        - health_check is in list (after server import)
        - is_tool_available() works correctly
        """
        # Import server to trigger tool registration
        import server  # noqa: F401

        from tools import get_available_tools, is_tool_available

        # get_available_tools returns a list
        tools = get_available_tools()
        assert isinstance(tools, list), "get_available_tools should return a list"

        # health_check should be registered
        assert "health_check" in tools, "health_check should be in available tools"

        # is_tool_available works
        assert is_tool_available("health_check") is True
        assert is_tool_available("nonexistent_tool") is False

    def test_get_tool_impl_returns_callable(self) -> None:
        """Test that get_tool_impl returns a callable function."""
        # Import server to trigger tool registration with impl
        import server  # noqa: F401

        from tools import get_tool_impl, TOOL_REGISTRY

        # Check if health_check is in the new-style registry
        if "health_check" in TOOL_REGISTRY:
            impl = get_tool_impl("health_check")
            assert callable(impl), "Tool implementation should be callable"

    def test_get_tool_impl_raises_for_unknown_tool(self) -> None:
        """Test that get_tool_impl raises KeyError for unknown tools."""
        from tools import get_tool_impl

        with pytest.raises(KeyError):
            get_tool_impl("nonexistent_tool")

    def test_register_tool_with_impl(self) -> None:
        """Test registering a tool with its implementation."""
        from tools import (
            register_tool,
            get_available_tools,
            get_tool_impl,
            AVAILABLE_TOOLS,
            TOOL_REGISTRY,
        )

        # Create a test tool
        def test_tool_impl(x: int) -> int:
            return x * 2

        # Clean up if test tool exists from previous run
        if "test_tool" in AVAILABLE_TOOLS:
            AVAILABLE_TOOLS.remove("test_tool")
        if "test_tool" in TOOL_REGISTRY:
            del TOOL_REGISTRY["test_tool"]

        # Register with implementation
        register_tool("test_tool", impl=test_tool_impl, description="A test tool")

        # Check it's available
        assert "test_tool" in get_available_tools()

        # Check implementation is retrievable
        impl = get_tool_impl("test_tool")
        assert impl is test_tool_impl
        assert impl(5) == 10

        # Clean up
        AVAILABLE_TOOLS.remove("test_tool")
        del TOOL_REGISTRY["test_tool"]
