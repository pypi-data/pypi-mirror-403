"""Workflow notification models for callbacks."""
from typing import Annotated

from pydantic import BaseModel, Field

from olmoearth_shared.api.run.prediction_results import PredictionResultResponse
from olmoearth_shared.api.run.workflow import (
    DatasetBuildFromWindowsWorkflowResult,
    FineTuningWorkflowResponse,
    WorkflowResponse,
)

WorkflowResultInfo = Annotated[
    FineTuningWorkflowResponse | PredictionResultResponse | DatasetBuildFromWindowsWorkflowResult,
    Field(discriminator='workflow_type')
]


class WorkflowNotification(BaseModel):
    """Structure of the payload sent to clients when emitting Workflow status update notifications"""

    workflow: WorkflowResponse = Field(description="The Workflow that triggered the notification")
    result_info: WorkflowResultInfo | None = Field(
        default=None,
        description="If the workflow is complete, this contains the workflow-specific results"
    )
    error_message: str | None = Field(
        default=None,
        description="Error details if the Workflow failed",
    )
