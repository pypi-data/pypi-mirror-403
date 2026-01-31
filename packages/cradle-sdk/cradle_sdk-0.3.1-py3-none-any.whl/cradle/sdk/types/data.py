from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, Field

from .common import (
    ArchivableResourceMixin,
    BaseListResponse,
    ContextProject,
    ContextRound,
    ContextWorkspace,
    ErrorResponseMixin,
    ImmutableResourceResponse,
    ResourceResponse,
)


class ArtifactProducerKind(StrEnum):
    TASK = "TASK"
    USER = "USER"


class DataActionKind(StrEnum):
    LOAD = "LOAD"
    UNDO_LOAD = "UNDO_LOAD"
    TABLE_CREATE = "TABLE_CREATE"
    TABLE_UPDATE = "TABLE_UPDATE"
    TABLE_ARCHIVE = "TABLE_ARCHIVE"


class DataLoadState(StrEnum):
    PENDING = "PENDING"
    LOADING = "LOADING"
    DELETING = "DELETING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FileFormat(StrEnum):
    CSV = "CSV"
    PARQUET = "PARQUET"
    NDJSON = "NDJSON"


class TableKind(StrEnum):
    TABLE = "TABLE"
    VIEW = "VIEW"


class TypeNames(StrEnum):
    BOOL = "BOOL"
    INT64 = "INT64"
    FLOAT64 = "FLOAT64"
    STRING = "STRING"
    STRUCT = "STRUCT"
    ARRAY = "ARRAY"


class AddTableRequest(BaseModel):
    table_ref: str
    config: TableLoadConfig


class ColumnBase(BaseModel):
    name: str
    metadata: ColumnMetadata | None = Field(default=None)


class ArrayType(BaseModel):
    type: Literal[TypeNames.ARRAY] = Field(default=TypeNames.ARRAY)
    item_type: PrimitiveType | StructType | ArrayType = Field(discriminator="type")


class ArtifactResponse(ImmutableResourceResponse):
    context: ContextWorkspace | ContextProject | ContextRound = Field(discriminator="kind")
    type: str
    data: dict[str, Any]
    producer: TaskProducer | UserProducer = Field(discriminator="kind")


class TableCreateBase(BaseModel):
    kind: TableKind
    reference: str = Field(
        description="A unique name to use for referring to the table, such as `temperature_assay`. User-created\ntables should always use this simple `table_name` format. Cradle-created table references have the form\n`catalog.schema.table_name`, for example `cradle.results.engineered_sequences`.\n\nReferences must be unique per workspace. One exception to the rule is that once a table is archived the\nrefence is available to be used again. References are tied to a data version, i.e. when running a query\nat a historic version, a reference will point to the table that held the reference at this data version."
    )
    description: str | None = Field(default=None, description="A human-friendly description of the table's contents.")


class TableResponseBase(ResourceResponse, ArchivableResourceMixin):
    """Base class for table responses."""

    kind: TableKind
    reference: str = Field(
        description="A unique name to use for referring to the table, such as `temperature_assay`. User-created\ntables should always use this simple `table_name` format. Cradle-created table references have the form\n`catalog.schema.table_name`, for example `cradle.results.engineered_sequences`.\n\nReferences must be unique per workspace. One exception to the rule is that once a table is archived the\nrefence is available to be used again. References are tied to a data version, i.e. when running a query\nat a historic version, a reference will point to the table that held the reference at this data version."
    )
    description: str | None
    columns: list[Annotated[PrimitiveColumn | StructColumn | ArrayColumn, Field(discriminator="type")]] = Field(
        description="The columns of the table. For views, the columns and their types are inferred from the query at view creation or update time."
    )
    version_id: int = Field(
        description="The version ID of the table state reflected in the response.Changes to a view's query or a base table's columns cause a version change as well as renames cause a version change."
    )


class _TableUpdateBase(BaseModel):
    description: str | None = Field(default=None, description="Description of the table.")


class ColumnMetadata(BaseModel):
    description: str | None = Field(default=None)
    deprecated: bool = Field(default=False)


class DataActionLoad(BaseModel):
    kind: Literal[DataActionKind.LOAD] = Field(default=DataActionKind.LOAD)
    load_id: int = Field(description="The ID of the data load from which data was added to the dataset.")


class DataActionTableArchive(BaseModel):
    kind: Literal[DataActionKind.TABLE_ARCHIVE] = Field(default=DataActionKind.TABLE_ARCHIVE)
    table_id: int = Field(description="The ID of the table that was archived.")


class DataActionTableCreate(BaseModel):
    kind: Literal[DataActionKind.TABLE_CREATE] = Field(default=DataActionKind.TABLE_CREATE)
    table_id: int = Field(description="The ID of the table that was created.")
    table_version_id: int = Field(description="The ID of the table version that was created.")


class DataActionTableUpdate(BaseModel):
    kind: Literal[DataActionKind.TABLE_UPDATE] = Field(default=DataActionKind.TABLE_UPDATE)
    table_id: int = Field(description="The ID of the table that was updated.")
    table_version_id: int = Field(description="The ID of the new table version.")


class DataActionUndoLoad(BaseModel):
    kind: Literal[DataActionKind.UNDO_LOAD] = Field(default=DataActionKind.UNDO_LOAD)
    load_id: int = Field(description="ID of the data load of which data was removed from the dataset.")


class DataLoadCreate(BaseModel):
    context: ContextProject | ContextRound = Field(
        description="The context the loaded data will be associated with. The data will either live within a Project (visible to all rounds) or within a specific Round of a project (visible only to that round)."
    )
    tables: dict[str, TableLoadConfig] = Field(
        default_factory=dict,
        description="A map of table references to table schemas. The map keys define the tables for which data is uploaded. The map values define the schema and file format for a given table.",
    )


class DataLoadResponse(ResourceResponse, ErrorResponseMixin):
    context: ContextWorkspace | ContextProject | ContextRound = Field(
        description="The context the loaded data is be associated with", discriminator="kind"
    )
    tables: dict[str, TableLoadConfigResponse] = Field(
        default_factory=dict, description="The tables for which data will be loaded."
    )
    state: DataLoadState
    is_active: bool
    files: list[FileUploadResponse] = Field(description="Files that have been uploaded to this data load.")


class DataVersionResponse(ImmutableResourceResponse):
    action: (
        DataActionLoad
        | DataActionUndoLoad
        | Annotated[DataActionTableCreate | DataActionTableUpdate | DataActionTableArchive, Field(discriminator="kind")]
    ) = Field(discriminator="kind")


class FileUploadResponse(ImmutableResourceResponse):
    filepath: str
    size: int
    table_reference: str | None
    source_file_id: int | None
    description: str | None


class ListArtifactResponse(BaseListResponse):
    items: list[ArtifactResponse]


class ListDataLoadResponse(BaseListResponse):
    items: list[DataLoadResponse]


class ListDataVersionResponse(BaseListResponse):
    items: list[DataVersionResponse]


class ListTableResponse(BaseListResponse):
    items: list[Annotated[BaseTableResponse | ViewTableResponse, Field(discriminator="kind")]]


class PrimitiveType(BaseModel):
    type: Literal[TypeNames.BOOL, TypeNames.INT64, TypeNames.FLOAT64, TypeNames.STRING]


class QueryDataRequest(BaseModel):
    query: str = Field(description="The SQL query to execute.")
    arrow_compression: Literal["zstd", "lz4"] | None = Field(
        default=None,
        description="The compression algorithm to use for the Arrow response. Supported values are `zstd`, `lz4`, and `None`(meaning no compression).",
    )
    project_id: int | None = Field(
        default=None, description="If set, the query will only run over data associated with the given `project_id`."
    )
    version_id: int | None = Field(
        default=None,
        description="If set, will run the query against the given version of the data according to the changelog.",
    )


class StructType(BaseModel):
    type: Literal[TypeNames.STRUCT] = Field(default=TypeNames.STRUCT)
    columns: list[Annotated[PrimitiveColumn | StructColumn | ArrayColumn, Field(discriminator="type")]]


class TableArchive(BaseModel):
    pass


class TableLoadConfig(BaseModel):
    columns: list[Annotated[PrimitiveColumn | StructColumn | ArrayColumn, Field(discriminator="type")]] = Field(
        description="The column layout of the files. All files in the data load destined for this table must have this exact column layout. For CSV files, only the specified columns determine how data is loaded. The first row (header) in each uploaded file is skipped. For Parquet files, columns will be matched by name and are thus not order-sensitive. Therefore it is recommended to use Parquet files for more robust data loading."
    )
    format: FileFormat


class TableRename(BaseModel):
    new_reference: str = Field(
        description="A unique name to use for referring to the table, such as `temperature_assay`. User-created\ntables should always use this simple `table_name` format. Cradle-created table references have the form\n`catalog.schema.table_name`, for example `cradle.results.engineered_sequences`.\n\nReferences must be unique per workspace. One exception to the rule is that once a table is archived the\nrefence is available to be used again. References are tied to a data version, i.e. when running a query\nat a historic version, a reference will point to the table that held the reference at this data version."
    )


class TaskProducer(BaseModel):
    kind: Literal[ArtifactProducerKind.TASK] = Field(default=ArtifactProducerKind.TASK)
    task_id: int


class UserProducer(BaseModel):
    kind: Literal[ArtifactProducerKind.USER] = Field(default=ArtifactProducerKind.USER)


class ArrayColumn(ColumnBase, ArrayType):
    """A column representing an array of elements.

    Unlike the other column types it is not nullable but the array can be empty.
    This matches BigQuery's behavior and reduces ambiguity.
    """


class BaseTableCreate(TableCreateBase):
    kind: Literal[TableKind.TABLE] = Field(
        default=TableKind.TABLE,
        description="Whether to create a *table* or a *view*. Tables are created with the purpose of uploading data\n        to them, while views are created as queries on top of existing tables or views. Think of tables as physical\n        entities that store data, while views are virtual entities that represent a query result.\n        ",
    )
    columns: list[Annotated[PrimitiveColumn | StructColumn | ArrayColumn, Field(discriminator="type")]] = Field(
        description="Columns of the table"
    )


class ViewTableCreate(TableCreateBase):
    kind: Literal[TableKind.VIEW] = Field(
        default=TableKind.VIEW,
        description="Whether to create a *table* or a *view*. Tables are created with the purpose of uploading data\n        to them, while views are created as queries on top of existing tables or views. Think of tables as physical\n        entities that store data, while views are virtual entities that represent a query result.\n        ",
    )
    query: str = Field(
        description="SQL query for the view. It must be a single SELECT statement with a limited, but still very powerful, subset of SQL. Subqueries, common table expressions, joins, and conditional expressions with all commonly used SQL operators are supported. Contact your customer success representative if you need to use a specific SQL feature that is not supported. If you have a query use case that is not covered by the currently permitted SQL expressions, contact support to discuss potential extensions."
    )
    columns: list[Annotated[PrimitiveColumn | StructColumn | ArrayColumn, Field(discriminator="type")]] | None = Field(
        default=None,
        description="Columns of the view. The column schema must match the query's result schema. If unspecified, a schema is automatically inferred from the query and column metadata will be copied over from the existing schema if the column already existed.",
    )


class BaseTableResponse(TableResponseBase):
    kind: Literal[TableKind.TABLE] = Field(default=TableKind.TABLE)


class ViewTableResponse(TableResponseBase):
    kind: Literal[TableKind.VIEW] = Field(default=TableKind.VIEW)
    query: str = Field(description="The SQL query that defines the view.")


class BaseTableUpdate(_TableUpdateBase):
    kind: Literal[TableKind.TABLE] = Field(default=TableKind.TABLE)
    columns: list[Annotated[PrimitiveColumn | StructColumn | ArrayColumn, Field(discriminator="type")]] | None = Field(
        default=None, description="Columns of the table."
    )


class ViewTableUpdate(_TableUpdateBase):
    kind: Literal[TableKind.VIEW] = Field(default=TableKind.VIEW)
    query: str | None = Field(
        default=None,
        description="SQL query for the view. It must be a single SELECT statement and only a subset of SQL is allowed. If unspecified, no change is made to the view query.If you have a query use case that is not covered by the currently permitted SQL expressions, contact support to discuss potential extensions.",
    )
    columns: list[Annotated[PrimitiveColumn | StructColumn | ArrayColumn, Field(discriminator="type")]] | None = Field(
        default=None,
        description="Columns of the view. The column schema must match the query's result schema. If unspecified, a schema is automatically inferred from the query and column metadata will be copied over from the existing schema if the column already existed.",
    )


class PrimitiveColumn(ColumnBase, PrimitiveType):
    """A column representing a primitive type."""

    nullable: bool = Field(default=True)


class StructColumn(ColumnBase, StructType):
    """A column representing a struct of fields."""

    nullable: bool = Field(default=True)


class TableLoadConfigResponse(TableLoadConfig):
    table_id: int | None = Field(
        description="The table the rows were loaded into. This is the table addressed by the table reference for this configuration at the time of finalization."
    )


Column: TypeAlias = Annotated[PrimitiveColumn | StructColumn | ArrayColumn, Field(discriminator="type")]
ColumnType: TypeAlias = Annotated[PrimitiveType | StructType | ArrayType, Field(discriminator="type")]
TableResponse: TypeAlias = Annotated[BaseTableResponse | ViewTableResponse, Field(discriminator="kind")]
