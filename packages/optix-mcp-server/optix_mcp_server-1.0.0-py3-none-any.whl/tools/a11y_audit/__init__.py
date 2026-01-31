"""Accessibility audit tool for MCP server.

Provides a 6-step guided workflow for auditing frontend applications
for WCAG 2.1/2.2 compliance. Generates A11Y-AUDIT.MD reports with
findings organized by severity and WCAG criterion.
"""

from tools.a11y_audit.domains import AccessibilityStepDomain
from tools.a11y_audit.finding import AccessibilityFinding
from tools.a11y_audit.report import A11yAuditReportGenerator
from tools.a11y_audit.severity import AccessibilitySeverity
from tools.a11y_audit.tool import AccessibilityAuditTool

__all__ = [
    "AccessibilityAuditTool",
    "AccessibilityFinding",
    "AccessibilitySeverity",
    "AccessibilityStepDomain",
    "A11yAuditReportGenerator",
]
