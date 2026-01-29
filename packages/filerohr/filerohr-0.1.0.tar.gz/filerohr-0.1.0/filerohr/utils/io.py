from contextlib import asynccontextmanager
import hashlib
import mimetypes
import os
from pathlib import Path
import shutil

import aiofiles
import aiofiles.os
from pebble import asynchronous


@asynchronous.thread
def mkfifo(path: Path):
    os.mkfifo(path)


@asynccontextmanager
async def create_tmp_file(*, delete_on_raise: bool = True, **kwargs):
    async with aiofiles.tempfile.NamedTemporaryFile(**kwargs) as tmp_file:
        try:
            yield Path(tmp_file.name)
        except Exception:
            if delete_on_raise:
                await remove_file(tmp_file.name)
            raise


@asynccontextmanager
async def create_fifo(path: Path):
    try:
        await mkfifo(path)
        yield path
    finally:
        await remove_file(path)


async def remove_file(path: Path):
    try:
        await aiofiles.os.unlink(path)
    except FileNotFoundError:
        pass


@asynchronous.thread
def rename_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(src, dst)


@asynchronous.thread
def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


@asynchronous.thread
def get_mime_type(path: Path):
    mime, _ = mimetypes.guess_file_type(path)
    return mime


async def symlink(pointing_to: Path, symlink_path: Path):
    await aiofiles.os.makedirs(symlink_path.parent, exist_ok=True)
    try:
        await aiofiles.os.symlink(pointing_to, symlink_path)
    except FileExistsError as exc:
        if Path(exc.filename) == pointing_to:
            return
        raise


@asynchronous.process
def hash_file(path: Path, *, alg: str = "sha256", prefix: bool = True):
    with path.open("rb") as f:
        file_hash = hashlib.file_digest(f, alg).hexdigest()
        return f"{alg}:{file_hash}" if prefix else file_hash
