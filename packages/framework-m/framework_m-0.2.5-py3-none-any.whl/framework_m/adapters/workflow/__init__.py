"""Workflow adapters for Framework M.

This package contains concrete implementations of WorkflowProtocol:
- InternalWorkflowAdapter: Database-backed workflow using DocTypes
- TemporalWorkflowAdapter: Integration with Temporal.io (optional)
"""

from framework_m.adapters.workflow.internal_workflow import InternalWorkflowAdapter
from framework_m.adapters.workflow.temporal_adapter import TemporalWorkflowAdapter

__all__ = ["InternalWorkflowAdapter", "TemporalWorkflowAdapter"]
