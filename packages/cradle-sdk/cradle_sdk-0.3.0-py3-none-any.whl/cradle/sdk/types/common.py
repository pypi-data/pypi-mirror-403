from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, Field


class AbstractResourceResponse(BaseModel):
    id: int = Field(description="The unique identifier of the resource")
    created_at: datetime = Field(description="The time at which the resource was created")
    created_by: str = Field(description="The ID of the user who created the resource")


class ArchivableResourceMixin(BaseModel):
    archived_at: datetime | None = Field(default=None, description="The time at which the resource was archived")
    archived_by: str | None = Field(default=None, description="The ID of the user who archived the resource")


class BaseListResponse(BaseModel):
    items: list[AbstractResourceResponse] = Field(description="The listed resources.")
    cursor: str | None = Field(
        description="Cursor with which the next page of entries can be retrieved. If no cursor is returned, no further pages exist."
    )


class ContextProject(BaseModel):
    kind: Literal["PROJECT"] = Field(default="PROJECT")
    project_id: int


class ContextRound(BaseModel):
    kind: Literal["ROUND"] = Field(default="ROUND")
    round_id: int


class ContextWorkspace(BaseModel):
    kind: Literal["WORKSPACE"] = Field(default="WORKSPACE")


class ErrorResponseMixin(BaseModel):
    """Mixin for resources that can return errors."""

    errors: list[str] = Field(default_factory=list, description="List of error messages associated with the resource.")


class ListOptions(BaseModel):
    limit: int = Field(default=100, description="Maximum number of items to return")
    cursor: str | None = Field(default=None, description="Continuation token returned by the previous page's response")
    order: Literal["ASC", "DESC"] = Field(
        default="ASC", description="Whether to order the result ascending or descending"
    )


class ImmutableResourceResponse(AbstractResourceResponse):
    pass


class ResourceResponse(AbstractResourceResponse):
    updated_at: datetime = Field(description="The time at which the resource was last updated")
    updated_by: str = Field(description="The ID of the user who last updated the resource")


Context: TypeAlias = Annotated[ContextWorkspace | ContextProject | ContextRound, Field(discriminator="kind")]
