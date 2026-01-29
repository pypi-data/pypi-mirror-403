import dataclasses
from collections import OrderedDict
from itertools import chain

from _hydrogenlib_core.typefunc import Function
from _hydrogenlib_cli.base.metadata.argument import Argument


@dataclasses.dataclass
class CommandMeta:
    name: str
    command: str
    description: str

    args: OrderedDict[str, Argument] = dataclasses.field(default_factory=OrderedDict)
    kwargs: dict[str, Argument] = dataclasses.field(default_factory=dict)
    switches: dict[str, Argument] = dataclasses.field(default_factory=dict)

    mutually_exclusive: set[str] = None
    requires: set[str] = None

    _short_names_ = None

    def __post_init__(self):
        self._short_names_ = {}
        for arg in chain(self.args.values(), self.kwargs.values(), self.switches.values()):
            if arg.short_name:
                self._short_names_[arg.short_name] = arg.name

    def get_fullname(self, name_or_short_name: str):
        if name_or_short_name in self._short_names_:
            return self._short_names_[name_or_short_name]
        else:
            return self._short_names_

    def get_argument(self, name: str):
        name = self.get_fullname(name)

        if arg := self.args.get(name):
            return arg
        elif arg := self.kwargs.get(name):
            return arg
        elif arg := self.switches.get(name):
            return arg
        else:
            return None


# Decorator
def command(
        func, *, name: str = None, description: str = None,
        command: str = None
):
    def decorator(func):
        func = Function(func)

        func.__command__ = cmd = CommandMeta(
            name or func.name,
            command or func.name,
            description or func.doc
        )
