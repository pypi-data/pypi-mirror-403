import httpx
from pydantic import AnyHttpUrl


class HttpUrlBuilder(httpx.URL):
    def __init__(
        self, url: httpx.URL | AnyHttpUrl | str, *, use_trailing_slash: bool = False, **kwargs
    ) -> None:
        if use_trailing_slash:
            url = httpx.URL(str(url))
            if not url.path.endswith("/"):
                url = url.copy_with(path=f"{url.path}/")
        super().__init__(str(url), **kwargs)
        self._use_trailing_slash = use_trailing_slash

    def __truediv__(self, other: str | int):
        sub_paths = str(other).split("/")
        new_path = self.path
        for path in sub_paths:
            if not new_path.endswith("/"):
                new_path += "/"
            new_path += path
        if self._use_trailing_slash:
            new_path += "/"
        return self.copy_with(path=new_path)

    def copy_with(self, **kwargs) -> "HttpUrlBuilder":
        cls = type(self)
        return cls(super().copy_with(**kwargs), use_trailing_slash=self._use_trailing_slash)

    @property
    def origin(self):
        origin = f"{self.scheme}://{self.host}"
        if self.port is not None:
            origin += f":{self.port}"
        return origin
