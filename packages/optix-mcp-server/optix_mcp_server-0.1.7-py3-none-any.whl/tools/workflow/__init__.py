"""MCP Workflow base classes for multi-step tool implementations.

This package provides abstract base classes and data models for implementing
workflow tools that operate in multiple steps with context accumulation.

Public Exports:
    WorkflowTool: Abstract base class for multi-step workflow tools
    WorkflowRequest: Input data model for workflow step requests
    WorkflowResponse: Output data model with continuation ID and results
    WorkflowState: Container for workflow session state
    WorkflowStateManager: Singleton for managing workflow states
    StepHistory: Data model for individual step records
    ConsolidatedFindings: Aggregated findings across all steps
    StepGuidance: Guidance for next workflow step
    ConfidenceLevel: Enum for confidence levels (exploring to certain)
    ValidationError: Exception for invalid request data
    validate_request: Function to validate workflow request data
"""

from tools.workflow.base import WorkflowTool
from tools.workflow.confidence import ConfidenceLevel
from tools.workflow.findings import ConsolidatedFindings
from tools.workflow.guidance import StepGuidance
from tools.workflow.request import WorkflowRequest
from tools.workflow.response import WorkflowResponse
from tools.workflow.state import StepHistory, WorkflowState, WorkflowStateManager
from tools.workflow.validation import ValidationError, validate_request

__all__ = [
    "ConfidenceLevel",
    "ConsolidatedFindings",
    "StepGuidance",
    "StepHistory",
    "ValidationError",
    "WorkflowRequest",
    "WorkflowResponse",
    "WorkflowState",
    "WorkflowStateManager",
    "WorkflowTool",
    "validate_request",
]
