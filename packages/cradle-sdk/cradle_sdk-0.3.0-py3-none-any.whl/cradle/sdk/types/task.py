from __future__ import annotations

from abc import ABC
from typing import TypeAlias

from pydantic import BaseModel, Field

from .common import (
    ArchivableResourceMixin,
    BaseListResponse,
    ContextProject,
    ContextRound,
    ContextWorkspace,
    ErrorResponseMixin,
    ResourceResponse,
)
from .tasks import v1, v2
from .tasks.common import TaskState


class ListTaskResponse(BaseListResponse):
    items: list[TaskResponse]


class TaskUpdateBase(BaseModel, ABC):
    display_name: str | None = Field(
        default=None, description="Optional display name for the task. This name is mutable."
    )
    description: str | None = Field(
        default=None, description="Optional description to provide additional notes about the executed task."
    )


class TaskResponse(ResourceResponse, ArchivableResourceMixin, ErrorResponseMixin):
    type: str
    context: ContextWorkspace | ContextProject | ContextRound = Field(
        description="The context in which this task runs. Tasks started in a project or round context will only 'see' table data that belongs to the associated project.",
        discriminator="kind",
    )
    name: str | None = Field(description="An optional name of the task.", deprecated="Use display_name instead.")
    display_name: str | None = Field(default=None, description="An optional display name of the task.")
    idempotency_key: str | None = Field(
        default=None,
        description="An optional idempotency key of the task. It must be unique within the task's context.",
    )
    description: str | None = Field(description="A description of the task.")
    data_version_id: int | None = Field(description="The data version at which table inputs are observed.")
    data_load_id: int | None = Field(description="ID of the data load for the task's results.")
    parameters: (
        v1.AnalyzeDataParameters
        | v1.AnalyzeDiversifyParameters
        | v1.AnalyzeEngineerParameters
        | v1.AnalyzeTrainParameters
        | v1.DiversifyParameters
        | v1.EngineerParameters
        | v1.SearchParameters
        | v1.SelectParameters
        | v1.TrainParameters
        | v2.AnalyzeDataParameters
        | v2.DiversifyParameters
        | v2.EngineerParameters
        | v2.SelectParameters
        | v2.SearchParameters
        | v2.TrainParameters
    ) = Field(description="The parameters of the task.")
    result: (
        v1.AnalyzeResult
        | v1.DiversifyResult
        | v1.EngineerResult
        | v1.SearchResult
        | v1.SelectResults
        | v1.TrainResult
        | v2.AnalyzeDataResult
        | v2.DiversifyResult
        | v2.EngineerResult
        | v2.SelectResult
        | v2.SearchResult
        | v2.TrainResult
        | None
    ) = Field(description="The result of the completed task.")
    state: TaskState = Field(description="The current state of the task's execution.")


class TaskCreate(TaskUpdateBase):
    parameters: (
        v1.AnalyzeDataParameters
        | v1.AnalyzeDiversifyParameters
        | v1.AnalyzeEngineerParameters
        | v1.AnalyzeTrainParameters
        | v1.DiversifyParameters
        | v1.EngineerParameters
        | v1.SearchParameters
        | v1.SelectParameters
        | v1.TrainParameters
        | v2.AnalyzeDataParameters
        | v2.DiversifyParameters
        | v2.EngineerParameters
        | v2.SelectParameters
        | v2.SearchParameters
        | v2.TrainParameters
    ) = Field(description="The parameters for the task.")
    context: ContextWorkspace | ContextProject | ContextRound = Field(
        description="The context in which the task is executed.", discriminator="kind"
    )
    data_version_id: int | None = Field(
        default=None,
        description="For tasks that have parameters referencing data tables, this specifies the version of the table data to use. If no version is specified, it defaults to the most recent data version.",
    )
    name: str | None = Field(
        default=None,
        description="Optional name for the task. If provided it will ensure that only one task with that name exists within the task's context. This field is deprecated in favor of display_name + idempotency_key.",
    )
    idempotency_key: str | None = Field(
        default=None,
        description="Optional idempotency key to ensure only one task with this key exists within its context. If provided and a task with this key already exists, the existing task will be returned instead of creating a new one.",
    )


class TaskUpdate(TaskUpdateBase):
    pass


TaskParameters: TypeAlias = (
    v1.AnalyzeDataParameters
    | v1.AnalyzeDiversifyParameters
    | v1.AnalyzeEngineerParameters
    | v1.AnalyzeTrainParameters
    | v1.DiversifyParameters
    | v1.EngineerParameters
    | v1.SearchParameters
    | v1.SelectParameters
    | v1.TrainParameters
    | v2.AnalyzeDataParameters
    | v2.DiversifyParameters
    | v2.EngineerParameters
    | v2.SelectParameters
    | v2.SearchParameters
    | v2.TrainParameters
)
TaskResults: TypeAlias = (
    v1.AnalyzeResult
    | v1.DiversifyResult
    | v1.EngineerResult
    | v1.SearchResult
    | v1.SelectResults
    | v1.TrainResult
    | v2.AnalyzeDataResult
    | v2.DiversifyResult
    | v2.EngineerResult
    | v2.SelectResult
    | v2.SearchResult
    | v2.TrainResult
)
