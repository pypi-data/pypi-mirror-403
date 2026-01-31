"""Report generators package.

Provides lens-specific report generators that transform WorkflowState
data into complete markdown reports.
"""

from tools.generate_report.generators.base import ReportGenerator
from tools.generate_report.generators.security import SecurityReportGenerator
from tools.generate_report.generators.a11y import A11yReportGenerator
from tools.generate_report.generators.devops import DevOpsReportGenerator
from tools.generate_report.generators.principal import PrincipalReportGenerator
from tools.generate_report.models import AuditLens

GENERATOR_MAP = {
    AuditLens.SECURITY: SecurityReportGenerator,
    AuditLens.A11Y: A11yReportGenerator,
    AuditLens.DEVOPS: DevOpsReportGenerator,
    AuditLens.PRINCIPAL: PrincipalReportGenerator,
}

__all__ = [
    "ReportGenerator",
    "SecurityReportGenerator",
    "A11yReportGenerator",
    "DevOpsReportGenerator",
    "PrincipalReportGenerator",
    "GENERATOR_MAP",
]
