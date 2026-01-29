import json
import time
from pathlib import Path

from cradle.sdk.types.data import FileUploadResponse
from cradle.sdk.types.task import TaskResponse

from .client import DataLoadClient, TaskClient


def upload_blob_files(
    client: DataLoadClient, load_id: int, files: list[Path], table_reference: str | None = None
) -> list[FileUploadResponse]:
    responses = []
    for f in files:
        response = client.upload_file(load_id=load_id, file=f, table_reference=table_reference)
        print(f"Uploaded {f}, id={response.id}")
        responses.append(response)
    return responses


def wait_for_task(client: TaskClient, task_id: int, timeout: float = 60) -> TaskResponse:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        task = client.get(task_id)
        print(f"\r{task.state} @ {task.updated_at}", end="", flush=True)
        if task.state == "COMPLETED":
            if task.result is None:
                raise ValueError("Task result is None")
            print()
            print(json.dumps(task.result.model_dump(mode="json"), indent=2))
            return task
        if task.state == "FAILED":
            print()
            print(task.errors)
            return task
        if task.state == "CANCELLED":
            return task
        time.sleep(1)
    return client.get(task_id)
