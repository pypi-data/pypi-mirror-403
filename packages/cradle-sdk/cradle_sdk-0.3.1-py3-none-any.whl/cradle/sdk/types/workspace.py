from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, RootModel

from .common import (
    ArchivableResourceMixin,
    BaseListResponse,
    ErrorResponseMixin,
    ImmutableResourceResponse,
    ResourceResponse,
)


class CustomPredictorInputDataType(StrEnum):
    BOOL = "BOOL"
    INT64 = "INT64"
    FLOAT64 = "FLOAT64"
    STRING = "STRING"


class CustomPredictorKind(StrEnum):
    CONTAINER = "CONTAINER"


class CustomPredictorState(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PROVISIONING = "PROVISIONING"
    FAILED = "FAILED"


class WorkspaceState(StrEnum):
    PROVISIONING = "PROVISIONING"
    DELETING = "DELETING"
    READY = "READY"
    DELETED = "DELETED"
    FAILED = "FAILED"


class CustomPredictorCreateMixin(BaseModel):
    name: str = Field(
        description="The custom predictor name with which it is referenced. Must be unique within the workspace and consist of only letters, numbers and the '-' character."
    )
    display_name: str = Field(description="The human-readable name of the predictor")
    description: str = Field(description="Comprehensive description of what the predictor does")
    url: HttpUrl | None = Field(
        default=None, description="Optional URL where to find more information about the predictor"
    )


class CustomPredictorUpdateMixin(BaseModel):
    inputs: list[CustomPredictorInput] = Field(description="List of input parameters that the predictor consumes")
    outputs: list[CustomPredictorOutput] = Field(
        description="List of outputs that the predictor produces for each sequence"
    )
    batch_size: int = Field(
        description="Number of sequences that the predictor should be invoked with. Note that the predictor can be invoked with fewer sequences, but will never be invoked with more."
    )


class CustomPredictorContainerMixin(BaseModel):
    kind: Literal[CustomPredictorKind.CONTAINER] = Field(default=CustomPredictorKind.CONTAINER)
    cpu_mcores: int = Field(description="CPU millicores to allocate for the custom predictor operating on one batch")
    main_memory_mib: int = Field(
        description="Main memory (RAM) to allocate for the custom predictor operating on one batch"
    )
    gpu_memory_mib: int = Field(
        description="If nonzero, GPU memory to allocate for the custom predictor operating on one batch"
    )


class CustomPredictorResponseMixin(ImmutableResourceResponse, ErrorResponseMixin):
    name: str
    display_name: str
    description: str
    url: str | None
    version_id: int
    state: CustomPredictorState
    inputs: list[CustomPredictorInput]
    outputs: list[CustomPredictorOutput]
    batch_size: int


class CustomPredictorCreate(RootModel):
    root: CustomPredictorContainerCreate = Field(discriminator="kind")


class CustomPredictorCreateResponse(RootModel):
    root: CustomPredictorContainerCreateResponse = Field(discriminator="kind")


class CustomPredictorInput(BaseModel):
    name: str
    description: str | None = Field(default=None)
    type: CustomPredictorInputDataType
    default_value: None | bool | str | int | float = Field(default=None)


class CustomPredictorOutput(BaseModel):
    assay_id: str
    name: str
    unit: str | None = Field(default=None)


class CustomPredictorResponse(RootModel):
    root: CustomPredictorContainerResponse = Field(discriminator="kind")


class CustomPredictorUpdate(RootModel):
    root: CustomPredictorContainerUpdate = Field(discriminator="kind")


class ListCustomPredictorResponse(BaseListResponse):
    items: list[CustomPredictorResponse]


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


class CustomPredictorContainerCreate(
    CustomPredictorCreateMixin, CustomPredictorUpdateMixin, CustomPredictorContainerMixin
):
    pass


class CustomPredictorContainerUpdate(CustomPredictorUpdateMixin, CustomPredictorContainerMixin):
    pass


class CustomPredictorContainerCreateResponse(CustomPredictorResponseMixin, CustomPredictorContainerMixin):
    upload_url: str
    upload_headers: dict[str, str]


class CustomPredictorContainerResponse(CustomPredictorResponseMixin, CustomPredictorContainerMixin):
    pass
