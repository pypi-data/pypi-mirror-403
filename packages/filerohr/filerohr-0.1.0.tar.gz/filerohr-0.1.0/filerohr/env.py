import os
import typing


class _Undefined:
    pass


def _noop(value: str) -> str:
    return value


class Environment:
    # TODO: remove all the typing.overload calls
    #       once https://github.com/python/mypy/issues/3737 has been fixed
    def __init__(self, prefix: str = ""):
        self.prefix = prefix

    def _gen_name(self, env_var_name: str):
        return f"{self.prefix}{env_var_name}"

    @typing.overload
    def get(
        self,
        env_var_name: str,
        *,
        cast: typing.Callable[[str], str] = _noop,
        default: str | type[_Undefined] = _Undefined,
        pop: bool = False,
    ) -> str: ...

    @typing.overload
    def get[T](
        self,
        env_var_name: str,
        *,
        cast: typing.Callable[[str], T],
        default: T | type[_Undefined] = _Undefined,
        pop: bool = False,
    ) -> T: ...

    def get[T](
        self,
        env_var_name: str,
        *,
        cast=_noop,
        default: T | type[_Undefined] = _Undefined,
        pop: bool = False,
    ) -> T:
        name = self._gen_name(env_var_name)
        try:
            value = os.environ[name]
        except KeyError:
            if default is not _Undefined:
                return typing.cast(T, default)
            raise
        else:
            if pop:
                del os.environ[name]
            return cast(value)

    @typing.overload
    def get_list(
        self,
        env_var_name: str,
        *,
        separator: str = ",",
        cast: typing.Callable[[str], str] = _noop,
        default: list[str] | type[_Undefined] = _Undefined,
        pop: bool = False,
    ) -> list[str]: ...

    @typing.overload
    def get_list[T](
        self,
        env_var_name: str,
        *,
        separator: str = ",",
        cast: typing.Callable[[str], T],
        default: list[T] | type[_Undefined] = _Undefined,
        pop: bool = False,
    ) -> list[T]: ...

    def get_list[T](
        self,
        env_var_name: str,
        *,
        separator: str = ",",
        cast=_noop,
        default: list[T] | type[_Undefined] = _Undefined,
        pop: bool = False,
    ) -> list[T]:
        try:
            value = self.get(env_var_name, pop=pop)
        except KeyError:
            if default is not _Undefined:
                return typing.cast(list[T], default)
            raise
        split_env = [v.strip() for v in value.split(separator)]
        return [cast(v) for v in split_env if v]

    def is_true(
        self,
        env_var_name: str,
        *,
        default: bool | type[_Undefined] = _Undefined,
        pop: bool = False,
    ) -> bool:
        try:
            value = self.get(env_var_name, pop=pop).lower()
        except KeyError:
            if default is not _Undefined:
                return typing.cast(bool, default)
            raise
        else:
            return value in {"1", "yes", "on", "true"}

    def __contains__(self, item):
        name = self._gen_name(item)
        return name in os.environ
