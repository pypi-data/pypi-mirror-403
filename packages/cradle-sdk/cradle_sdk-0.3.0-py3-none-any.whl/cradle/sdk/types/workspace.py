from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from .common import ArchivableResourceMixin, BaseListResponse, ErrorResponseMixin, ResourceResponse


class WorkspaceState(StrEnum):
    PROVISIONING = "PROVISIONING"
    DELETING = "DELETING"
    READY = "READY"
    DELETED = "DELETED"
    FAILED = "FAILED"


class ListProjectResponse(BaseListResponse):
    items: list[ProjectResponse]


class ListRoundResponse(BaseListResponse):
    items: list[RoundResponse]


class ProjectCreate(BaseModel):
    name: str


class ProjectResponse(ResourceResponse, ArchivableResourceMixin):
    name: str


class RoundCreate(BaseModel):
    project_id: int = Field(description="The project to which the round belongs")
    name: str = Field(description="The name of the round")
    description: str | None = Field(default=None)


class RoundResponse(ResourceResponse, ArchivableResourceMixin):
    project_id: int
    name: str
    description: str | None


class WorkspaceResponse(ResourceResponse, ErrorResponseMixin):
    name: str
    display_name: str
    state: WorkspaceState
    picture_file_id: int | None = Field(default=None)
