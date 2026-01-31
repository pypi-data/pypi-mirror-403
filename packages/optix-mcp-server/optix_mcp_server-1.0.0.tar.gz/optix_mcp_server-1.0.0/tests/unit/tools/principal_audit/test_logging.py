"""Tests for PrincipalAuditTool logging integration."""

import pytest
from unittest.mock import patch, MagicMock

from tools.principal_audit.tool import PrincipalAuditTool


class TestPrincipalAuditLogging:
    """Tests for logging integration."""

    def test_tool_uses_get_logger(self):
        """Tool should use _get_logger() inherited from WorkflowTool."""
        tool = PrincipalAuditTool()
        logger = tool._get_logger()
        assert logger is not None
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'warn')
        assert hasattr(logger, 'info')

    def test_log_method_uses_logger_debug_for_info(self):
        """_log method should use logger.debug() for non-error messages."""
        tool = PrincipalAuditTool()
        with patch.object(tool, '_get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            tool._log("Test message")
            mock_logger.debug.assert_called_once_with("Test message")

    def test_log_method_uses_logger_warn_for_errors(self):
        """_log method should use logger.warn() for error messages."""
        tool = PrincipalAuditTool()
        with patch.object(tool, '_get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            tool._log("Error message", error=True)
            mock_logger.warn.assert_called_once_with("Error message")

    def test_execute_produces_log_messages(self):
        """Execute should produce log messages via logger."""
        tool = PrincipalAuditTool()
        with patch.object(tool, '_get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            tool.execute(
                step_number=1,
                next_step_required=True,
                files_examined=["src/main.py"],
                confidence="exploring",
            )
            assert mock_logger.debug.called or mock_logger.info.called
