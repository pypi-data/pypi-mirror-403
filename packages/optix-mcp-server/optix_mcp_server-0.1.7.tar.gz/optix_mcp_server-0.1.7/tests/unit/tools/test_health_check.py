"""Unit tests for health_check tool implementation.

These tests verify that the health_check tool can be called directly
without MCP context, making it MCP-agnostic and independently testable.
"""

import pytest


class TestHealthCheckImpl:
    """Tests for health_check_impl function."""

    def test_health_check_impl_direct_call(self) -> None:
        """Test that health_check_impl works without MCP context.

        Verifies:
        - Function callable without MCP imports
        - Returns dict with expected structure
        - Values match provided parameters
        """
        # Import the implementation directly - no MCP needed
        from tools.health_check.core import health_check_impl

        # Call directly with test data
        result = health_check_impl(
            server_name="test-server",
            version="1.0.0",
            uptime_seconds=123.456,
            available_tools=["tool1", "tool2"],
        )

        # Verify it's a dict
        assert isinstance(result, dict), "Result should be a dictionary"

        # Verify structure
        assert "status" in result
        assert "server_name" in result
        assert "version" in result
        assert "uptime_seconds" in result
        assert "tools_available" in result

    def test_health_check_impl_returns_expected_structure(self) -> None:
        """Test that health_check_impl returns correct values.

        Verifies:
        - All provided parameters are in the result
        - Status is determined correctly based on tools
        - Uptime is rounded correctly
        """
        from tools.health_check.core import health_check_impl

        result = health_check_impl(
            server_name="my-server",
            version="2.0.0",
            uptime_seconds=99.999,
            available_tools=["health_check", "analyze"],
        )

        # Check values
        assert result["server_name"] == "my-server"
        assert result["version"] == "2.0.0"
        assert result["uptime_seconds"] == 100.0  # Rounded
        assert result["tools_available"] == ["health_check", "analyze"]
        assert result["status"] == "healthy"  # Has tools

    def test_health_check_impl_degraded_when_no_tools(self) -> None:
        """Test that status is degraded when no tools available."""
        from tools.health_check.core import health_check_impl

        result = health_check_impl(
            server_name="test-server",
            version="1.0.0",
            uptime_seconds=0,
            available_tools=[],
        )

        assert result["status"] == "degraded"

    def test_health_check_impl_filters_disabled_tools(self) -> None:
        """Test that disabled tools are filtered from available list."""
        from tools.health_check.core import health_check_impl

        result = health_check_impl(
            server_name="test-server",
            version="1.0.0",
            uptime_seconds=0,
            available_tools=["tool1", "tool2", "tool3"],
            disabled_tools=["tool2"],
        )

        assert "tool1" in result["tools_available"]
        assert "tool2" not in result["tools_available"]
        assert "tool3" in result["tools_available"]

    def test_health_check_impl_degraded_when_all_tools_disabled(self) -> None:
        """Test status is degraded when all tools are disabled."""
        from tools.health_check.core import health_check_impl

        result = health_check_impl(
            server_name="test-server",
            version="1.0.0",
            uptime_seconds=0,
            available_tools=["tool1"],
            disabled_tools=["tool1"],
        )

        assert result["status"] == "degraded"
        assert result["tools_available"] == []
