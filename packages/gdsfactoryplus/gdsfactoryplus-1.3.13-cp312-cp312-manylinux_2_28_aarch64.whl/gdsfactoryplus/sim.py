"""Simulation API."""

from __future__ import annotations

import secrets
import time
from collections.abc import Iterable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx
from pydantic import BaseModel

__all__ = []

BASE_URL = "https://simulation.dev.gdsfactory.com/api/simulation/v1"
USER_ID = "00000000-0000-0000-0000-000000000000"
ORG_ID = "00000000-0000-0000-0000-000000000000"
TIMEOUT = 30.0


class SimStatus(str, Enum):
    """Simulation job status."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobDefinition(str, Enum):
    """Available job definition names."""

    FEMWELL = "dev-femwell-simulation"
    MEEP = "dev-meep-simulation"
    PALACE = "dev-palace-simulation"


class Job(BaseModel):
    """Simulation job data."""

    id: str
    job_name: str
    status: SimStatus
    container_image: str
    submitted_by: str
    organization_id: str
    created_at: datetime
    job_definition_revision: int
    output_size_bytes: int
    job_def_name: str
    queue_name: str | None = None
    exit_code: int | None = None
    finished_at: datetime | None = None
    started_at: datetime | None = None
    status_reason: str | None = None
    detail_reason: str | None = None
    requested_cpu: float | None = None
    requested_memory_mb: int | None = None
    download_urls: dict[str, str] | None = None


class PrepareJobResponse(BaseModel):
    """Response for job prepare request."""

    upload_url: str
    job_id: str


class OutputDownloadResponse(BaseModel):
    """Response for output download URLs."""

    total_size_bytes: int
    download_urls: dict[str, str]


class UploadFileResponse(BaseModel):
    """Response for file upload to S3."""

    key: str
    etag: str
    content_length: int


class PreJob(BaseModel):
    """Result from upload_simulation."""

    job_id: str
    job_name: str


def upload_simulation(
    path: str | Path,
    job_definition: str | JobDefinition,
    job_name: str | None = None,
    job_queue_name: str | None = None,
) -> PreJob:
    """Upload simulation input file and return upload result."""
    path = Path(path)
    job_definition_name = (
        job_definition.value
        if isinstance(job_definition, JobDefinition)
        else job_definition
    )
    if not job_name:
        job_name = f"{job_definition_name}-{secrets.token_hex(4)}"
    prepare_response = _prepare_job(
        job_name, path.name, job_definition_name, job_queue_name
    )
    _upload_file(prepare_response.upload_url, path)
    return PreJob(
        job_id=prepare_response.job_id,
        job_name=job_name,
    )


def start_simulation(pre_job: PreJob) -> Job:
    """Start a simulation job with the uploaded input."""
    return _submit_job(pre_job.job_id)


def wait_for_simulation(job: Job, poll_interval: float = 5.0) -> Job:
    """Wait for simulation to complete, polling at the specified interval."""
    last_len = 0
    while job.status not in (SimStatus.COMPLETED, SimStatus.FAILED):
        created = job.created_at.strftime("%H:%M:%S")
        now = datetime.now(job.created_at.tzinfo).strftime("%H:%M:%S")
        msg = f"Created: {created} | Now: {now} | Status: {job.status.value}"
        print(f"\r{msg.ljust(last_len)}", end="", flush=True)  # noqa: T201
        last_len = len(msg)
        time.sleep(poll_interval)
        job = get_job(job.id)
    created = job.created_at.strftime("%H:%M:%S")
    now = datetime.now(job.created_at.tzinfo).strftime("%H:%M:%S")
    msg = f"Created: {created} | Now: {now} | Status: {job.status.value}"
    print(f"\r{msg.ljust(last_len)}")  # noqa: T201
    return job


def download_results(
    job: Job,
    output_dir: str | Path | None = None,
    keep: Iterable[str] = (),
    skip: Iterable[str] = (),
) -> dict[str, Path]:
    """Download all simulation output files to the specified directory."""
    output_dir = Path(output_dir or job.job_name).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    download_urls = (
        job.download_urls
        if job.download_urls
        else _get_output_download_urls(job.id).download_urls
    )
    downloaded_files: dict[str, Path] = {}
    for name, url in download_urls.items():
        if keep and name not in keep:
            continue
        if skip and name in skip:
            continue
        parsed = urlparse(url)
        filename = Path(unquote(parsed.path)).name
        path = output_dir / filename
        _download_file(url, path)
        downloaded_files[name] = path
    return downloaded_files


def run_simulation(
    path: str | Path,
    job_definition: str | JobDefinition,
    output_dir: str | Path | None = None,
    job_name: str | None = None,
    job_queue_name: str | None = None,
    poll_interval: float = 5.0,
) -> dict[str, Path]:
    """Run a complete simulation: upload, start, wait, and download."""
    pre_job = upload_simulation(path, job_definition, job_name, job_queue_name)
    job = start_simulation(pre_job)
    job = wait_for_simulation(job, poll_interval)
    return download_results(job, output_dir)


def get_job(job_id: str) -> Job:
    """Get a simulation job by ID."""
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.get(
            f"{BASE_URL}/job/{job_id}",
            headers=_headers(),
        )
        response.raise_for_status()
        data = response.json()
    job = Job.model_validate(data["data"])
    if job.status == SimStatus.COMPLETED:
        download_response = _get_output_download_urls(job.id)
        job.download_urls = download_response.download_urls
    return job


def _headers() -> dict[str, str]:
    return {
        "X-User-Id": USER_ID,
        "X-Org-Id": ORG_ID,
        "Content-Type": "application/json",
    }


def _prepare_job(
    job_name: str,
    original_file_name: str,
    job_definition_name: str,
    job_queue_name: str | None = None,
) -> PrepareJobResponse:
    """Prepare a simulation job and get presigned upload URL."""
    payload: dict[str, Any] = {
        "job_name": job_name,
        "original_file_name": original_file_name,
        "job_definition_name": job_definition_name,
    }
    if job_queue_name:
        payload["job_queue_name"] = job_queue_name
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(
            f"{BASE_URL}/job/prepare",
            headers=_headers(),
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return PrepareJobResponse.model_validate(data["data"])


def _submit_job(job_id: str) -> Job:
    """Submit a simulation job for execution."""
    payload = {"job_id": job_id}
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(
            f"{BASE_URL}/job/submit",
            headers=_headers(),
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return Job.model_validate(data["data"])


def _get_output_download_urls(job_id: str) -> OutputDownloadResponse:
    """Get presigned download URLs for simulation job output."""
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.get(
            f"{BASE_URL}/job/{job_id}/output/download-url",
            headers=_headers(),
        )
        response.raise_for_status()
        data = response.json()["data"]
        data["download_urls"] = {
            Path(url.split("?")[0]).name: url for url in data.get("download_urls", [])
        }
        return OutputDownloadResponse.model_validate(data)


def _upload_file(upload_url: str, path: str | Path) -> UploadFileResponse:
    """Upload a file to S3 using a presigned URL."""
    path = Path(path)
    with path.open("rb") as f:
        content = f.read()
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.put(upload_url, content=content)
        response.raise_for_status()
    parsed = urlparse(upload_url)
    key = unquote(parsed.path.lstrip("/").split("/", 1)[1])
    return UploadFileResponse(
        key=key,
        etag=response.headers.get("ETag", "").strip('"'),
        content_length=len(content),
    )


def _download_file(download_url: str, path: str | Path) -> None:
    """Download a file from S3 using a presigned URL."""
    path = Path(path)
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.get(download_url)
        response.raise_for_status()
    with path.open("wb") as f:
        f.write(response.content)
