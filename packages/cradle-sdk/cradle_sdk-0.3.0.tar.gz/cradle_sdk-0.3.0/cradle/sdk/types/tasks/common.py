from __future__ import annotations

from abc import ABC
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class TaskState(StrEnum):
    INIT = "INIT"
    PREPARING_INPUTS = "PREPARING_INPUTS"
    LAUNCHING = "LAUNCHING"
    EXECUTING = "EXECUTING"
    LOADING_RESULTS = "LOADING_RESULTS"
    CANCELLING = "CANCELLING"
    RECOVERING = "RECOVERING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ArtifactParam(BaseModel):
    artifact_id: int


class ParametersBase(BaseModel, ABC):
    """Class that marks top-level task inputs. Used for static checks."""


class ResultBase(BaseModel, ABC):
    """Class that marks top-level task results. Used for static checks."""


class TableOutputBase(BaseModel):
    table: str = Field(description="The reference to the table the result was written to.")


class TableSourceQuery(BaseModel):
    kind: Literal["QUERY"] = Field(default="QUERY")
    query: str


class TableSourceTable(BaseModel):
    kind: Literal["TABLE"] = Field(default="TABLE")
    table: str


class TableSourceTaskResult(BaseModel):
    kind: Literal["TASK_RESULT"] = Field(default="TASK_RESULT")
    table: str
    task_id: int | list[int]


class TableResult(TableOutputBase):
    pass
