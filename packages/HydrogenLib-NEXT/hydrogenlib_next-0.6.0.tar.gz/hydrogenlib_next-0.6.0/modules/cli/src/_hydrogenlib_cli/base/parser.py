from abc import ABC, abstractmethod
from typing import Protocol


class ParseResult(Protocol):
    command_line: list[str]
    switches: set[str]
    positional_args: list[str]
    keyword_args: dict[str, str]


class AbstractParser(ABC):
    @abstractmethod
    def parse(self, argv: list[str]) -> dict: ...
