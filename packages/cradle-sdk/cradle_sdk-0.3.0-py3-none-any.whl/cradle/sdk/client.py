import copy
import difflib
import logging
import time
from collections.abc import Iterator
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Any, BinaryIO, NoReturn, TypeVar
from urllib.parse import urlparse

import httpx
import jwt
import pyarrow as pa
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Generator, override

from cradle.sdk.auth.device import DeviceAuth
from cradle.sdk.exceptions import ClientError as ClientError  # for re-export
from cradle.sdk.types.common import (
    ContextProject,
    ContextRound,
    ContextWorkspace,
    ListOptions,
)
from cradle.sdk.types.data import (
    AddTableRequest,
    ArtifactResponse,
    BaseTableCreate,
    BaseTableUpdate,
    DataLoadCreate,
    DataLoadResponse,
    DataVersionResponse,
    FileUploadResponse,
    ListArtifactResponse,
    ListDataLoadResponse,
    ListDataVersionResponse,
    ListTableResponse,
    QueryDataRequest,
    TableArchive,
    TableRename,
    TableResponse,
    ViewTableCreate,
    ViewTableUpdate,
)
from cradle.sdk.types.task import (
    ListTaskResponse,
    TaskCreate,
    TaskResponse,
    TaskState,
)
from cradle.sdk.types.workspace import (
    ListProjectResponse,
    ListRoundResponse,
    ProjectCreate,
    ProjectResponse,
    RoundCreate,
    RoundResponse,
    WorkspaceResponse,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class HttpClient:
    def __init__(
        self,
        prefix: str,
        base_url: str,
        auth: httpx.Auth | None = None,
        timeout: float = 60.0,
        user_agent: str | None = None,
        workspace: str | None = None,
        use_keyring: bool = True,
    ):
        base_url = base_url.rstrip("/")
        user_agent = user_agent or f"cradle-sdk-python/{pkg_version('cradle-sdk')}"
        headers = {
            "Accept": "application/json",
            "User-Agent": user_agent,
        }
        client = httpx.Client(auth=auth, headers=headers, timeout=timeout, follow_redirects=True)
        if auth is None:
            client.auth = DeviceAuth.from_strategy(
                client=client, workspace=workspace, base_url=base_url, use_keyring=use_keyring
            )

        self.http_client = client
        self.prefix = prefix.strip("/")
        self.base_url = base_url.rstrip("/")
        self.workspace = workspace

    def with_prefix(self, prefix: str) -> "HttpClient":
        c = copy.copy(self)
        c.prefix = f"{self.prefix}/{prefix.strip('/')}".strip("/")
        return c

    def url(self, path: str) -> str:
        """Generate a URL for a given path.

        This follows slightly weird rules, specific to how our API is designed.

        The overall goal here is to make the URL generation loose with what it accepts, to never
        be confused by whether or not there are unexpected slashes in any part of the url. It's a very
        "do what I mean" approach.

        - "path" is never interpreted as an absolute path, it is always relative to the prefix
        - if the path starts with ":", it is a verb endpoint and should be appended to the url + prefix, not assumed to be a subpath
        - everything else is assumed to be a subpath and should be appended to the url + prefix
        """

        combined_path = f"{self.prefix}{path}"
        if not path.startswith(":") and not path.startswith("/"):
            combined_path = f"{self.prefix}/{path}"

        # This special case is needed in case we have a ":verb" endpoint at the root of the API
        # like "https://cradle.bio/:list" - otherwise the logic below would generate
        # "https://cradle.bio:list" which is wrong.
        parsed_url = urlparse(self.base_url)
        base_url_has_path = bool(parsed_url.path and parsed_url.path not in {"", "/"})
        if combined_path.startswith(":") and base_url_has_path:
            return f"{self.base_url}{combined_path}"

        return f"{self.base_url}/{combined_path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | BaseModel | None = None,
        params: dict[str, Any] | None = None,
        **kwargs,
    ) -> httpx.Response:
        if params is not None:
            # HTTPX will send "...&foo=&...", which FastAPI would interpret as an empty string rather than None.
            kwargs["params"] = {k: v for k, v in params.items() if v is not None}
        if isinstance(json, BaseModel):
            json = json.model_dump(mode="json", by_alias=True)
        if json is not None:
            kwargs["json"] = json

        return self.http_client.request(method, self.url(path), **kwargs)

    def get(self, path: str, response_type: type[T] | Any | None, params: dict[str, Any] | None = None, **kwargs) -> T:
        return self._handle_response(self.request("GET", path, params=params, **kwargs), response_type)

    def post(self, path: str, response_type: type[T] | Any | None, params: dict[str, Any] | None = None, **kwargs) -> T:
        return self._handle_response(self.request("POST", path, params=params, **kwargs), response_type)

    def _handle_response(
        self, response: httpx.Response, response_type: type[T] | Iterator[str] | Iterator[bytes] | None
    ) -> Any:
        if not response.is_success:
            self.handle_error_response(response)
        if response_type is None:
            return None

        ct = response.headers.get("content-type")
        if ct is None:
            raise ValueError("content type header missing")

        ct = ct.split(";")[0].strip()
        if ct == "application/json":
            return TypeAdapter(response_type).validate_python(response.json())
        if ct == "application/x-ndjson" and response_type == Iterator[str]:
            return response.iter_lines()
        if ct == "application/octet-stream" and response_type == Iterator[bytes]:
            return response.iter_bytes()
        raise ValueError(f"Unsupported content type {ct}")

    def handle_error_response(self, response: httpx.Response) -> NoReturn:
        auth = self.http_client.auth
        if (
            response.status_code == 403
            and self.workspace is not None
            and isinstance(auth, DeviceAuth)
            and auth.authorized_workspace_id != self.workspace
        ):
            auth.suggest_logout(self.workspace)
        try:
            body = response.json()
            error_msg = body.get("detail", response.text)
            if (error_id := body.get("error_id")) is not None:
                error_msg = f"{error_msg} (error ID: {error_id})"
            errors = body.get("errors", [])
        except Exception:  # noqa: BLE001
            error_msg = response.text
            errors = []
        raise ClientError(response.status_code, error_msg, errors=errors)


class DisabledAuth(httpx.Auth):
    """Auth implementation to use when authentication should be disabled"""

    def __init__(self, workspace: str | None = None):
        self._workspace_name = workspace

    @override
    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        claims = {
            "urn:cradle:email": "john-doe@cradle.bio",
            "urn:cradle:user_id": "john-doe",
            "urn:cradle:full_name": "John Doe",
            "urn:cradle:workspace_id": self._workspace_name,
        }

        token = jwt.encode(claims, key="none")

        request.headers["Authorization"] = f"Bearer ca_{token}"
        yield request


API_URL = "https://api.cradle.bio"


class Client:
    """The workspace API provides functionality for retrieving information about your workspace.

    A workspace is the home for all data, projects and tasks for an organization. By
    design no information can be shared across workspaces, they are the top-level
    concept in the Cradle API.

    Workspace creation and management is only available to Cradle administrators.
    """

    def __init__(
        self,
        workspace: str,
        auth: httpx.Auth | None = None,
        base_url: str = API_URL,
        timeout: int = 60,
        user_agent: str | None = None,
        use_keyring: bool = True,
    ):
        self._base_client = HttpClient(
            prefix="/",
            base_url=base_url,
            auth=auth,
            timeout=timeout,
            user_agent=user_agent,
            workspace=workspace,
            use_keyring=use_keyring,
        )
        self._client = self._base_client.with_prefix(f"/v2/workspace/{workspace}/")
        self._workspace = workspace

    def workspace(self) -> WorkspaceResponse:
        return self._base_client.get("/v2/workspace:get", WorkspaceResponse, dict(name=self._workspace))

    @property
    def project(self) -> "ProjectClient":
        return ProjectClient(self._client)

    @property
    def round(self) -> "RoundClient":
        return RoundClient(self._client)

    @property
    def data(self) -> "DataClient":
        return DataClient(self._client)

    @property
    def task(self) -> "TaskClient":
        return TaskClient(self._client)


class ProjectClient:
    """The projects API provides functionality for managing and interacting with
    projects in a workspace.

    Projects organize tasks in a workspace and represent the work involved in
    optimizing a specific protein or achieving a specific goal. Data is currently
    isolated to a specific project, but in the future we will support cross project
    data sharing within a workspace.
    """

    def __init__(self, client: HttpClient):
        self._client = client.with_prefix("/project")

    def get(self, project_id: int) -> ProjectResponse:
        """Get a project by `ID`."""
        return self._client.get(":get", ProjectResponse, dict(id=project_id))

    def list(self) -> Generator[ProjectResponse, None, None]:
        """List all projects in the workspace."""
        opts = ListOptions()
        while True:
            resp = self._client.get(":list", ListProjectResponse, params=opts.model_dump())
            yield from resp.items
            if resp.cursor is None:
                return
            opts.cursor = resp.cursor

    def get_by_name(self, name: str) -> ProjectResponse:
        """Get a project by name. Raises ValueError if not found."""
        for project in self.list():
            if project.name == name:
                return project
        raise ValueError(f"Project with name '{name}' not found")

    def create(self, project: ProjectCreate) -> ProjectResponse:
        """Create a new project in the workspace."""
        return self._client.post(":create", ProjectResponse, json=project)

    def update(self, project_id: int, project: ProjectCreate) -> ProjectResponse:
        """Update a project's information."""
        return self._client.post(":update", ProjectResponse, dict(id=project_id), json=project)

    def archive(self, project_id: int) -> ProjectResponse:
        """Archive a project.

        The data from the project will still be available.
        It will not be possible to create new tasks, data loads, etc. in the project.
        """
        return self._client.post(":archive", ProjectResponse, dict(id=project_id))

    def unarchive(self, project_id: int) -> ProjectResponse:
        """Unarchive a previously archived project.

        Returns an HTTP 422 `Unprocessable Entity` error if the project is not archived.
        """
        return self._client.post(":unarchive", ProjectResponse, dict(id=project_id))


class RoundClient:
    """The rounds API provides functionality for managing and interacting with rounds within a project.

    Rounds are a way to organize the experiments within a project. Commonly, a round represents all
    in-vitro experiments related to a specific sub-goal or timeframe of a project.
    While rounds are typically ordered sequentially, multiple rounds can exist in parallel (for example, when
    testing multiple design methods in parallel).

    Tasks, data loads, and reports can be (but don't have to be!) assigned to a round.
    """

    def __init__(self, client: HttpClient):
        self._client = client.with_prefix("/round")

    def get(self, round_id: int) -> RoundResponse:
        """Get a round by ID."""
        return self._client.get(":get", RoundResponse, dict(id=round_id))

    def list(self, project_id: int | None = None) -> Generator[RoundResponse, None, None]:
        """List all rounds in the project."""
        params = {}
        if project_id is not None:
            params["project_id"] = project_id

        opts = ListOptions()
        while True:
            resp = self._client.get(
                ":list",
                ListRoundResponse,
                params={**opts.model_dump(), **params},
            )
            yield from resp.items
            if resp.cursor is None:
                return
            opts.cursor = resp.cursor

    def get_by_name(self, project_id: int, name: str) -> RoundResponse:
        """Get a round by name within a specific project. Raises ValueError if not found."""
        for round_ in self.list(project_id=project_id):
            if round_.name == name:
                return round_
        raise ValueError(f"Round with name '{name}' not found in project {project_id}")

    def create(self, round_: RoundCreate) -> RoundResponse:
        """Create a new round in a project."""
        return self._client.post(":create", RoundResponse, json=round_)

    def update(self, round_id: int, round_: RoundCreate) -> RoundResponse:
        """Update a round's name and description."""
        return self._client.post(":update", RoundResponse, dict(id=round_id), json=round_)

    def archive(self, round_id: int) -> RoundResponse:
        """Archive a round.

        The data from the round will still be available.
        It will not be possible to create new tasks, data loads, etc. in the round.
        """
        return self._client.post(":archive", RoundResponse, dict(id=round_id))

    def unarchive(self, round_id: int) -> RoundResponse:
        """Unarchive a previously archived round.

        Returns an HTTP 422 `Unprocessable Entity` error if the round is not archived.
        """
        return self._client.post(":unarchive", RoundResponse, dict(id=round_id))


class DataClient:
    """The data API provides functionality for managing and interacting with data in a workspace.

    Data comes in the form of *tables* and *artifacts*.
    *Tables* are used to store row-based data, such as measurements, sequences, and other structured data.
    *Artifacts* are used to store the results of tasks, such as machine learning models, predictions, and other outputs.

    While tables can be created and uploaded by users, artifacts are only produced by tasks and cannot be uploaded directly.

    Artifacts and table rows (via their data load source) have a context specified. This context refers to the
    origin of the data and is used in other parts of the API to determine data visibility, e.g. to
    isolate data between projects.

    See the [Artifacts](#tag/Artifacts) API endpoints for more details on artifact data.

    See the [Tables](#tag/Tables) API endpoints for more details on tabular data.
    """

    def __init__(self, client: HttpClient):
        self._client = client.with_prefix("/data")

    @property
    def artifact(self) -> "ArtifactClient":
        return ArtifactClient(self._client)

    @property
    def table(self) -> "TableClient":
        return TableClient(self._client)

    @property
    def load(self) -> "DataLoadClient":
        return DataLoadClient(self._client)

    def list_versions(
        self,
        project_id: int | None = None,
        table_id: int | None = None,
    ) -> Generator[DataVersionResponse, None, None]:
        params = {}
        if project_id is not None:
            params["project_id"] = project_id
        if table_id is not None:
            params["table_id"] = table_id

        opts = ListOptions()
        while True:
            resp = self._client.get("/version:list", ListDataVersionResponse, params={**params, **opts.model_dump()})
            yield from resp.items
            if resp.cursor is None:
                return
            opts.cursor = resp.cursor


class ArtifactClient:
    """Artifacts are produced by tasks and can be referenced as inputs to other tasks. They can generally
    not be uploaded and downloaded directly. They have a well-defined type that determines for which
    purpose they can be used.
    """

    def __init__(self, client: HttpClient):
        self._client = client.with_prefix("/artifact")

    def get(self, artifact_id: int) -> ArtifactResponse:
        """Get information about an artifact."""
        return self._client.get(":get", ArtifactResponse, dict(id=artifact_id))

    def list(
        self,
        project_id: int | None = None,
        round_id: int | None = None,
    ) -> Generator[ArtifactResponse, None, None]:
        """List artifacts in the workspace."""
        opts = ListOptions()

        params = {}
        if project_id is not None:
            params["project_id"] = project_id
        if round_id is not None:
            params["round_id"] = round_id

        while True:
            resp = self._client.get(
                ":list",
                ListArtifactResponse,
                params={**opts.model_dump(), **params},
            )
            yield from resp.items
            if resp.cursor is None:
                return
            opts.cursor = resp.cursor


class _IteratorReader:
    def __init__(self, iterator: Iterator[bytes]):
        self.iterator = iterator
        self.buffer = b""
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True
        self._buffer = b""

    def read(self, size=-1):
        try:
            while size < 0 or len(self.buffer) < size:
                self.buffer += next(self.iterator)
        except StopIteration:
            pass
        if size < 0:
            out, self.buffer = self.buffer, b""
        else:
            out, self.buffer = self.buffer[:size], self.buffer[size:]
        return out

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class TableClient:
    """Tables store row-based data with a well-defined column schema. Such data may come from spreadsheets
    or other tabular data stores.

    Each table is created with a well-defined column schema, which can include primitive columns such
    as numbers and strings, as well as nested struct columns and arrays.
    A table's schema can be extended but existing columns cannot generally be modified or removed.

    Table data as well as it's column schema itself are version controlled. Each change to the contained
    rows is tracked as a data version.
    Tables can be queried at any historic version unless some destructive change has been made, such as
    hard deletion of historic data for compliance reasons.

    Because tables are versioned, each row is immutable. This means that it is not possible to change individual
    values in a row. Instead, the data load that added the row can be undone and the rows can be loaded
    again with the changed data.

    See the [Data Loads](#tag/Data-Loads) API endpoints on how to add and remove data to tables.
    """

    def __init__(self, client: HttpClient):
        self._client = client.with_prefix("/table")

    def query(
        self,
        query: str,
        *,
        project_id: int | None,
        version_id: int | None = None,
    ) -> Generator[pa.RecordBatch, None, None]:
        """Query data with the given SQL query and retrieve the result as arrow record batches.

        Args:
            query: The SQL query the execute.
            project_id: project_id to filter the source data by. Can be set to none to query data
                access all projects the authenticated user has access to.
            version_id: Data version ID at which to execute the query.

        Example:
            ```
            result = client.query("SELECT * FROM source_table")
            table = pyarrow.Table.from_batches(result)

            # Write as CSV. Does only work with primitive columns.
            pyarrow.csv.write_csv(t, "result.csv")

            # Write as Parquet. Does work with structs and array columns as well.
            pyarrow.parquet.write_table(t, "result.parquet")
            ```
        """
        request = QueryDataRequest(
            query=query,
            project_id=project_id,
            version_id=version_id,
        )
        with self._client.http_client.stream(
            "POST", self._client.url(":query"), json=request.model_dump(by_alias=True)
        ) as response:
            if not response.is_success:
                response.read()  # Required in streaming request to the error handling can access content.
                self._client.handle_error_response(response)

            ct = response.headers.get("content-type")
            if ct is None:
                raise ValueError("content type header missing")
            ct = ct.split(";")[0].strip()

            if ct != "application/vnd.apache.arrow.stream":
                raise ValueError(f"unexpected content type {ct}")
            yield from pa.ipc.open_stream(_IteratorReader(response.iter_bytes()))

    def get_by_id(self, table_id: int) -> TableResponse:
        """Retrieve the table by its ID.
        The ID is an opaque identifier for the table returned at table creation time and is distinct from the table reference.
        """
        return self._client.get(":getById", TableResponse, dict(id=table_id))

    def get(self, reference: str) -> TableResponse:
        """Get a table by its reference."""
        return self._client.get(":get", TableResponse, dict(reference=reference))

    def list(self) -> Generator[TableResponse, None, None]:
        """List all current base tables and views in the workspace."""
        opts = ListOptions()
        while True:
            resp = self._client.get(":list", ListTableResponse, params=opts.model_dump())
            yield from resp.items
            if resp.cursor is None:
                return
            opts.cursor = resp.cursor

    def list_versions(self, table_id: int) -> Generator[TableResponse, None, None]:
        """List all versions of a specific table."""
        opts = ListOptions()
        while True:
            resp = self._client.get(
                ":listVersions",
                ListTableResponse,
                params=dict(**opts.model_dump(), id=table_id),
            )
            yield from resp.items
            if resp.cursor is None:
                return
            opts.cursor = resp.cursor

    def list_archived(self, reference: str) -> Generator[TableResponse, None, None]:
        """List all archived tables that match the given reference."""
        opts = ListOptions()
        while True:
            resp = self._client.get(
                ":listArchived",
                ListTableResponse,
                params=dict(**opts.model_dump(), reference=reference),
            )
            yield from resp.items
            if resp.cursor is None:
                return
            opts.cursor = resp.cursor

    def create(self, table: ViewTableCreate | BaseTableCreate) -> TableResponse:
        """Create a new table or view."""
        return self._client.post(":create", TableResponse, json=table)

    def update(self, reference: str, table: ViewTableUpdate | BaseTableUpdate) -> TableResponse:
        """Update a table or view.

        Tables can only be updated in forward-compatible ways.
        New columns can be added but not be removed.
        Existing columns can be turned from non-nullable to nullable but not the other way around.
        Existing columns cannot be renamed or changed in type.

        Views can be updated arbitrarily.
        """
        return self._client.post(":update", TableResponse, params=dict(reference=reference), json=table)

    def archive(self, reference: str, archive: TableArchive | None = None) -> TableResponse:
        """Archive a table or view.

        Archiving makes the table or view inaccessible for regular operations
        but preserves it for historical purposes.
        """
        if not archive:
            archive = TableArchive()
        return self._client.post(":archive", TableResponse, params=dict(reference=reference), json=archive)

    def unarchive(self, table_id: int) -> TableResponse:
        """Unarchive a previously archived table or view.

        This makes the table or view available for regular operations again.
        If an active table with the same reference already exists, the unarchive operation
        will fail with an HTTP 409 `Conflict error`.
        """
        return self._client.post(":unarchive", TableResponse, params=dict(id=table_id))

    def rename(self, reference: str, rename: TableRename) -> TableResponse:
        """Rename the table."""
        return self._client.post(":rename", TableResponse, params=dict(reference=reference), json=rename)


class DataLoadClient:
    """The data API provides functionality for managing and interacting with data in a workspace.

    Data comes in the form of *tables* and *artifacts*.
    *Tables* are used to store row-based data, such as measurements, sequences, and other structured data.
    *Artifacts* are used to store the results of tasks, such as machine learning models, predictions, and other outputs.

    While tables can be created and uploaded by users, artifacts are only produced by tasks and cannot be uploaded directly.

    Artifacts and table rows (via their data load source) have a context specified. This context refers to the
    origin of the data and is used in other parts of the API to determine data visibility, e.g. to
    isolate data between projects.

    See the [Artifacts](#tag/Artifacts) API endpoints for more details on artifact data.

    See the [Tables](#tag/Tables) API endpoints for more details on tabular data.
    """

    def __init__(self, client: HttpClient):
        self._client = client.with_prefix("/load")

    def list(
        self, project_id: int | None = None, round_id: int | None = None
    ) -> Generator[DataLoadResponse, None, None]:
        """List all data loads in the workspace."""
        params = {}
        if project_id is not None:
            params["project_id"] = project_id
        if round_id is not None:
            params["round_id"] = round_id

        opts = ListOptions()
        while True:
            resp = self._client.get(":list", ListDataLoadResponse, params={**params, **opts.model_dump()})
            yield from resp.items
            if resp.cursor is None:
                return
            opts.cursor = resp.cursor

    def get(self, load_id: int) -> DataLoadResponse:
        """Get a data load by ID."""
        return self._client.get(":get", DataLoadResponse, dict(id=load_id))

    def create(self, load: DataLoadCreate) -> DataLoadResponse:
        """Create a new data load.
        After creation, the data load will be empty. Files can subsequently be added using the `uploadFile` endpoint.
        """
        return self._client.post(":create", DataLoadResponse, json=load)

    def upload_file(
        self,
        load_id: int,
        file: Path,
        *,
        description: str | None = None,
        filepath: str | Path | None = None,
        table_reference: str | None = None,
        source_file_id: int | None = None,
    ) -> FileUploadResponse:
        """Upload a file to the cloud storage bucket and add upload information to load."""
        data = {}
        if description is not None:
            data["description"] = description
        if filepath is not None:
            data["filepath"] = str(filepath)
        if table_reference is not None:
            data["table_reference"] = table_reference
        if source_file_id is not None:
            data["source_file_id"] = source_file_id

        with file.open("rb") as f:
            return self._client.post(
                ":uploadFile",
                FileUploadResponse,
                params=dict(id=load_id),
                files=dict(file=(file.name, f, "application/octet-stream")),
                data=data,
            )

    def download_file(self, file_id: str, buffer: BinaryIO):
        """Download a previously uploaded file from a load."""
        bytes_stream: Iterator[bytes] = self._client.get(":downloadFile", Iterator[bytes], dict(file_id=file_id))
        buffer.writelines(bytes_stream)

    def finalize(self, load_id: int) -> DataLoadResponse:
        """Finalize the data load and start ingesting rows from the uploaded files.

        The ingestion process will run in the background. The progress can be tracked by polling the data load
        and waiting for the status to switch from `LOADING` to `COMPLETED` or `FAILED`.
        """
        return self._client.post(":finalize", DataLoadResponse, params=dict(id=load_id))

    def delete(self, load_id: int) -> DataLoadResponse:
        """Delete the data load if it has not been completed yet.

        The deletion will happen asynchronously afterwards and is irreversible.
        """
        return self._client.post(":delete", DataLoadResponse, params=dict(id=load_id))

    def undo(self, load_id: int) -> DataLoadResponse:
        """Append an entry to the changelog undoing the load.

        The rows from this data load will no longer show at subsequent data versions.
        Previously undone loads can be redone to restore their data.
        """
        return self._client.post(":undo", DataLoadResponse, params=dict(id=load_id))

    def redo(self, load_id: int) -> DataLoadResponse:
        """Append an entry to the changelog redoing the load. The rows from this data load will be visible again at subsequent data versions."""
        return self._client.post(":redo", DataLoadResponse, params=dict(id=load_id))

    def add_table(self, load_id: int, request: AddTableRequest) -> DataLoadResponse:
        """Register a new table in the data load configuration."""
        return self._client.post(":addTable", DataLoadResponse, params=dict(id=load_id), json=request)


class TaskClient:
    """Create endpoints for all supported task types.

    When creating a task, a context must be specified. The context determines data visibility: data can either be visible
    in the entire project, or only in a specific round within a project.
    Artifact and table data also has a context and a task can only access data with a compatible context. A data context
    is compatible when it a workspace context or, if it is a project or round context, belongs to the same project.

    For example, suppose project `A` has rounds `abc` and `def` and project `B` has round `xyz`.
    A task with context `project=A` or `round=abc` can only see data with context `project=A` or `round=abc` or `round=def`.
    A task with context `project=B` can only see data with context `project=B` or `round=xyz`.

    Any data a task creates will be saved with the same context as the task.

    Tasks always use the latest version of the data in the workspace, unless a specific version is provided.
    """

    def __init__(self, client: HttpClient):
        self._client = client.with_prefix("/task")

    def list(self, project_id: int | None = None, round_id: int | None = None) -> Generator[TaskResponse, None, None]:
        """List all tasks in a workspace, project or round.

        To list all tasks in a workspace, leave `project_id` and `round_id` unset.
        To list all tasks in a project, specify `project_id` and leave `round_id` unset.
        To list all tasks in a round, specify `round_id` and leave `project_id` unset.

        Only one of `project_id` or `round_id` must be specified at once.
        """
        params = {}
        if project_id is not None:
            params["project_id"] = project_id
        if round_id is not None:
            params["round_id"] = round_id

        opts = ListOptions()
        while True:
            resp = self._client.get(":list", ListTaskResponse, params={**params, **opts.model_dump()})
            yield from resp.items
            if resp.cursor is None:
                return
            opts.cursor = resp.cursor

    def get(self, task_id: int) -> TaskResponse:
        """Obtain the current state and the result of a task.

        This endpoint can be called periodically to monitor the status of a task and to detect
        when it finished executing.

        If the `state` field of the response is `COMPLETED`, then the `result` field contains the
        task result (often containing IDs of artifacts and tables created by the task).

        If the `state` field of the response is `FAILED`, then the `error` field contains
        a description explaining why the task has failed.

        The states `COMPLETED`, `FAILED` and `CANCELLED` are terminal states. When the task is in
        any other state, it will eventually transition into one of these three.
        """
        return self._client.get(":get", TaskResponse, dict(id=task_id))

    def get_by_name(
        self,
        name: str,
        project_id: int | None = None,
        round_id: int | None = None,
    ) -> TaskResponse:
        """Get a task by unique name within their workspace, project, or round context.

        If a task with name "TaskA" exists in project with ID 123, the `project_id` must be specified.
        It is not sufficient to leave it unset as tasks with the same name may exist at the workspace or
        round context or in a different project.
        """
        tasks = self.list(project_id=project_id, round_id=round_id)
        # When listing for workspace or project we still need to filter it down since they'll
        # return tasks from their sub-contexts.
        if round_id is not None:
            scope_desc = f"round {round_id}"
            tasks = [task for task in tasks if task.context == ContextRound(round_id=round_id)]
        elif project_id is not None:
            scope_desc = f"project {project_id}"
            tasks = [task for task in tasks if task.context == ContextProject(project_id=project_id)]
        else:
            scope_desc = "workspace"
            tasks = [task for task in tasks if task.context == ContextWorkspace()]

        for task in tasks:
            if task.name == name:
                return task
        raise ValueError(f"Task with name '{name}' not found in {scope_desc}")

    def create(self, task: TaskCreate) -> TaskResponse:
        return self._client.post(f"/{task.parameters.task_type}:create", TaskResponse, json=task)

    def create_or_get(self, task: TaskCreate, skip_parameter_check: bool = False) -> TaskResponse:
        """Create a task or get existing one with matching (name or idempotency key) and parameters.

        The task must have a name or an idempotency key set. If the parameter check is not skipped the existing task must have
        the same parameters as `task`. If an explicit `data_version_id` is specified, it must also match.

        Raises ValueError if parameters don't match or if name is None.
        """

        error_prefix: str = ""

        # If you're using idempotency_key, the :create endpoint is already an upsert.
        if task.idempotency_key is not None:
            error_prefix = f"Task with idempotency key '{task.idempotency_key}'"
            existing_task = self.create(task)
        elif name := task.name:
            error_prefix = f"Task with name '{name}'"
            try:
                if isinstance(task.context, ContextRound):
                    existing_task = self.get_by_name(name, round_id=task.context.round_id)
                elif isinstance(task.context, ContextProject):
                    existing_task = self.get_by_name(name, project_id=task.context.project_id)
                else:
                    existing_task = self.get_by_name(name)
            except ValueError:
                existing_task = None
        else:
            raise ValueError("Task must have `name` or `idempotency_key` set")

        if existing_task is None:
            return self.create(task)

        if skip_parameter_check:
            return existing_task

        if existing_task.parameters != task.parameters:
            existing_params = existing_task.parameters.model_dump_json(indent=2, by_alias=True)
            new_params = task.parameters.model_dump_json(indent=2, by_alias=True)
            diff = "\n".join(
                difflib.unified_diff(
                    existing_params.splitlines(),
                    new_params.splitlines(),
                    fromfile="existing_parameters",
                    tofile="new_parameters",
                    lineterm="",
                )
            )
            raise ValueError(f"{error_prefix} exists but has different parameters:\n{diff}")

        if task.data_version_id is not None and existing_task.data_version_id != task.data_version_id:
            raise ValueError(
                f"{error_prefix} exists but has different data_version_id (existing: {existing_task.data_version_id}, new: {task.data_version_id})"
            )

        return existing_task

    def cancel(self, task_id: int) -> TaskResponse:
        """Cancel the task if possible.

        Only tasks that have not yet terminated may be canceled. There is no guarantee that cancellation succeeds
        before the task successfully completes.
        """
        return self._client.post(":cancel", TaskResponse, dict(id=task_id))

    def recover(self, task_id: int) -> TaskResponse:
        """Recover a task that has failed or been cancelled by putting it into state EXECUTING.

        Note that this is best-effort and is not guaranteed to fix any issues in the underlying
        backend execution, and may also cause unexpected side-effects such as duplicate data loads.
        Main use-case is tasks that failed due to intermittent issues in the backend which have been resolved.
        """
        return self._client.post(":recover", TaskResponse, dict(id=task_id))

    def archive(self, task_id: int) -> TaskResponse:
        """Archive the task.

        This will make the task disappear from regular task listings. It will not remove data that has been
        produced by the task. If data removal is required, use the `data_load_id` for the task's results
        and call the `/data/load:undo` endpoint separately.
        """
        return self._client.post(":archive", TaskResponse, dict(id=task_id))

    def unarchive(self, task_id: int) -> TaskResponse:
        """Unarchive the task."""
        return self._client.post(":unarchive", TaskResponse, dict(id=task_id))

    def wait(self, task_id: int, timeout: float = 60.0) -> TaskResponse:
        start = time.monotonic()

        while time.monotonic() - start < timeout:
            try:
                task = self.get(task_id)
                if task.state == TaskState.FAILED:
                    raise ValueError(f"Task {task_id} failed: {task.errors}")
                if task.state == TaskState.CANCELLED:
                    raise ValueError(f"Task {task_id} was cancelled")
                if task.state == TaskState.COMPLETED:
                    break
            except httpx.TransportError:
                logger.warning("Transport error while waiting for task, retrying...")
            except ClientError as e:
                if 500 <= e.status_code < 600:
                    logger.warning("Internal server error while waiting for task, retrying...")
                else:
                    raise

            time.sleep(3)
        print()
        return self.get(task_id)
