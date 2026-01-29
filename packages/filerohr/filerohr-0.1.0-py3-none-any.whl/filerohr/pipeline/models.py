import datetime
from pathlib import Path, PurePath
import urllib.parse
import uuid

from pydantic import AnyHttpUrl, BaseModel, Field

from filerohr.utils import now


class Licensing(BaseModel):
    authors: list[str]
    source_url: AnyHttpUrl | None = None
    spdx_identifier: str | None = None


class File(BaseModel):
    name: str
    path: Path | str
    id: uuid.uuid4 = Field(default_factory=uuid.uuid4)
    hash: str | None = None
    mime_type: str | None = None
    created_at: datetime.datetime = Field(default_factory=now)
    licensing: Licensing | None = None
    keep: bool = False
    log: str = ""

    def clone(self, cls: type["File"] | None = None, **kwargs):
        if cls is None:
            cls = type(self)
        new_attrs = {"keep": False} if "path" in kwargs else {}
        new_attrs.update(kwargs)
        data = self.model_copy(deep=True).model_dump()
        data.update(new_attrs)
        del data["id"]
        if "path" in kwargs and "hash" not in kwargs:
            del data["hash"]
        return cls(**data)

    @classmethod
    def from_path(cls, path: Path | str, **kwargs):
        path_str = str(path)
        url = urllib.parse.urlparse(path_str)
        if url.scheme:
            return cls.from_url(path_str, **kwargs)
        return cls.from_filesystem(Path(path), **kwargs)

    @staticmethod
    def from_filesystem(path: Path, **kwargs):
        return LocalFile(name=path.stem, path=path, **kwargs)

    @staticmethod
    def from_url(url: str, **kwargs):
        name = PurePath(urllib.parse.urlparse(url).path).name
        return RemoteFile(name=name, path=url, **kwargs)


class RemoteFile(File):
    path: str


class LocalFile(File):
    path: Path


class _AVMixin:
    duration: datetime.timedelta | None = Field(default=None)


class AudioMetadata(BaseModel):
    album: str = ""
    artist: str = ""
    isrc: str = ""
    organization: str = ""
    title: str = ""
    date: str = ""
    genre: str = ""

    def merge(self, other: "AudioMetadata", overwrite: bool = False) -> "AudioMetadata":
        all_fields = set(type(self).model_fields.keys())
        self_set_fields = self.model_fields_set
        other_set_fields = other.model_fields_set
        iter_fields = all_fields if overwrite else all_fields - self_set_fields
        iter_fields &= other_set_fields
        update = other.model_dump(include=iter_fields)
        return self.model_copy(update=update)


class _AudioMixin(_AVMixin):
    metadata: AudioMetadata = Field(default_factory=AudioMetadata)


class LocalAVFile(_AVMixin, LocalFile):
    pass


class LocalAudioFile(_AudioMixin, LocalFile):
    pass
