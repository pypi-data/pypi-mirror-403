"""Interact with the Figshare API."""

from pathlib import Path
from typing import Any

import pystow
import requests
from pydantic import BaseModel, ByteSize, HttpUrl
from tqdm.contrib import tmap
from tqdm.contrib.concurrent import thread_map

__all__ = [
    "File",
    "ensure_files",
    "get_files",
]

BASE_URL = "https://api.figshare.com/v2/articles"
MODULE = pystow.module("figshare")


class File(BaseModel):
    """An object representing a file in Figshare."""

    id: int
    name: str
    size: ByteSize
    is_link_only: bool
    download_url: HttpUrl
    supplied_md5: str | None = None
    computed_md5: str | None = None
    mimetype: str | None = None


def get_files(record_id: int) -> list[File]:
    """Get files for a record."""
    url = f"{BASE_URL}/{record_id}/files"
    res = requests.get(url, timeout=5)
    res.raise_for_status()
    return [File.model_validate(f) for f in res.json()]


def ensure_files(
    record_id: int, *, concurrent: bool = True, tqdm_kwargs: dict[str, Any] | None = None
) -> dict[Path, File]:
    """Ensure all files for a record."""
    files = get_files(record_id)
    submodule = MODULE.module(str(record_id))

    def _func(file: File) -> tuple[Path, File]:
        return submodule.ensure(url=str(file.download_url), name=file.name), file

    _tqdm_kwargs = {
        "desc": f"downloading figshare:{record_id}",
        "unit": "file",
        "leave": False,
    }
    if tqdm_kwargs:
        _tqdm_kwargs.update(tqdm_kwargs)

    if concurrent:
        return dict(thread_map(_func, files, **_tqdm_kwargs))
    else:
        return dict(tmap(_func, files, **_tqdm_kwargs))
