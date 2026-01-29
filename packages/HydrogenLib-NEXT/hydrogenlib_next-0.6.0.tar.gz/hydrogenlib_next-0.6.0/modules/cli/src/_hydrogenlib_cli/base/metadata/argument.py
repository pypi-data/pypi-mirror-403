import dataclasses
import enum
import typing
from typing import Any, Literal

type Validator[T = Any] = typing.Callable[[str], T]


class ArgumentTypes(str, enum.Enum):
    positional = "positional"
    keyword = "keyword"
    switch = "switch"


@dataclasses.dataclass
class Argument:
    name: str
    short_name: str = None
    description: str = None
    help: str = None
    default: Any = None
    validator: Validator = None
    type: Literal["positional", "keyword", "switch"] | ArgumentTypes = 'positional'
    nargs: int | Literal['*', '?'] | None = None
