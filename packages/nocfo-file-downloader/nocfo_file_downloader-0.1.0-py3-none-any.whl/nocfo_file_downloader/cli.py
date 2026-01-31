#!/usr/bin/env python3
"""NoCFO attachment downloader CLI."""

from __future__ import annotations

import getpass
import os
import threading
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Tuple
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import typer
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

app = typer.Typer(
    add_completion=False,
    help="Download NoCFO attachments and organize them by document number.",
)

DEFAULT_BASE_URL = "https://api-prd.nocfo.io"
DEFAULT_PAGE_SIZE = 200
DEFAULT_CONCURRENCY = 4

_thread_local = threading.local()


def _prompt_token(token: Optional[str]) -> str:
    """Return a PAT token, prompting the user if needed."""
    if token and token.strip():
        return token.strip()
    return getpass.getpass("Enter your NoCFO PAT token: ").strip()


def _build_session(token: str) -> requests.Session:
    """Create a requests session with the Authorization header set."""
    session = requests.Session()
    session.headers.update({"Authorization": f"Token {token}"})
    return session


def _get_thread_session(token: str) -> requests.Session:
    """Return a thread-local session to make concurrent requests safe."""
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = _build_session(token)
        _thread_local.session = session
    return session


def _get_basename(attachment: dict) -> str:
    """Resolve a stable filename for an attachment."""
    name = (attachment.get("name") or "").strip()
    if name:
        safe_name = name.replace("\\", "/")
        base_name = safe_name.rsplit("/", 1)[-1].strip()
        if base_name:
            return base_name
    file_url = (attachment.get("file") or "").strip()
    return os.path.basename(urlparse(file_url).path) or "attachment"


def _document_attachment_index(documents: Iterable[dict]) -> Dict[int, str]:
    """Build a map of attachment_id -> document_number."""
    index: Dict[int, str] = {}
    for document in documents:
        number = (document.get("number") or "").strip()
        if not number:
            continue
        for attachment_id in document.get("attachment_ids") or []:
            index[int(attachment_id)] = number
    return index


def _get_all_results(
    session: requests.Session,
    url: str,
    params: dict,
) -> Tuple[int, Iterator[dict]]:
    """Fetch paginated results and return the total count plus an iterator."""
    response = session.get(url, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    total = int(payload.get("count", 0))
    first_results = list(payload.get("results", []))
    next_value = payload.get("next")

    def _iterator() -> Iterator[dict]:
        yield from first_results
        nonlocal next_value
        while next_value:
            if isinstance(next_value, int):
                page_response = session.get(
                    url, params={**params, "page": next_value}, timeout=60
                )
            else:
                page_response = session.get(next_value, timeout=60)
            page_response.raise_for_status()
            page_payload = page_response.json()
            yield from page_payload.get("results", [])
            next_value = page_payload.get("next")

    return total, _iterator()


def _download_file(file_url: str, target_path: Path) -> None:
    """Stream a remote file to disk without API auth headers."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(file_url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with target_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)


def _download_attachment(file_url: str, target_path: Path) -> None:
    """Download one attachment."""
    _download_file(file_url, target_path)


def _build_target_path(
    output_dir: Path,
    attachment: dict,
    attachment_to_document: Dict[int, str],
) -> Path:
    """Build the local output path for an attachment."""
    attachment_id = int(attachment.get("id"))
    base_name = _get_basename(attachment)
    document_number = attachment_to_document.get(attachment_id)

    if document_number:
        file_name = f"{document_number} {base_name}".strip()
        return output_dir / document_number / file_name

    return output_dir / "UNCATEGORIZED" / base_name


@app.callback(invoke_without_command=True)
def main(
    business_slug: str = typer.Argument(
        ..., help="NoCFO business slug (single required parameter)."
    ),
    output_dir: Path = typer.Option(
        Path("downloads"),
        "--output-dir",
        "-o",
        help="Directory where files will be saved.",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        help="NoCFO PAT token. If omitted, you will be prompted.",
    ),
    base_url: str = typer.Option(
        DEFAULT_BASE_URL,
        "--base-url",
        help="NoCFO API base URL.",
    ),
    page_size: int = typer.Option(
        DEFAULT_PAGE_SIZE,
        "--page-size",
        help="Page size for API pagination.",
    ),
    concurrency: int = typer.Option(
        DEFAULT_CONCURRENCY,
        "--concurrency",
        "-c",
        help="Number of concurrent downloads.",
    ),
) -> None:
    """
    Download all attachments for a business and organize them by document number.

    The tool first fetches all documents and builds a map of
    document_number -> attachment_ids. Then it downloads every attachment and
    stores it under <document_number>/<document_number> <filename>. Attachments
    without a document association are stored under UNCATEGORIZED.
    """

    token_value = _prompt_token(token)
    if not token_value:
        raise typer.BadParameter("PAT token is required.")

    session = _build_session(token_value)

    documents_url = f"{base_url}/v1/business/{business_slug}/document/"
    files_url = f"{base_url}/v1/business/{business_slug}/files/"

    typer.echo("Fetching documents...")
    _, documents_iter = _get_all_results(
        session, documents_url, {"page_size": page_size}
    )
    attachment_index = _document_attachment_index(documents_iter)

    typer.echo("Fetching attachments...")
    total_files, attachments_iter = _get_all_results(
        session, files_url, {"page_size": page_size}
    )

    if total_files == 0:
        typer.echo("No attachments found.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    if concurrency < 1:
        raise typer.BadParameter("Concurrency must be at least 1.")

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task_id = progress.add_task("Downloading", total=total_files)
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for attachment in attachments_iter:
                target_path = _build_target_path(
                    output_dir, attachment, attachment_index
                )
                file_url = attachment.get("file")
                name = attachment.get("name") or target_path.name
                futures.append(
                    executor.submit(_download_attachment, file_url, target_path)
                )
                futures[-1].attachment_name = name

            for future in as_completed(futures):
                try:
                    future.result()
                except requests.HTTPError as exc:
                    progress.console.print(
                        f"[red]Failed[/red] {getattr(future, 'attachment_name', '')}: {exc}"
                    )
                except requests.RequestException as exc:
                    progress.console.print(
                        f"[red]Failed[/red] {getattr(future, 'attachment_name', '')}: {exc}"
                    )
                except Exception as exc:  # pragma: no cover - unexpected failures
                    progress.console.print(
                        f"[red]Failed[/red] {getattr(future, 'attachment_name', '')}: {exc}"
                    )
                progress.advance(task_id)

    typer.echo("Done.")


if __name__ == "__main__":
    app()
