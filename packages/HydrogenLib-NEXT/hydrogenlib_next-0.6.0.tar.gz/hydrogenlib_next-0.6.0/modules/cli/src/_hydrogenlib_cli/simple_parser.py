from _hydrogenlib_cli.base.metadata.command import CommandMeta


class Parser:
    def __init__(self, command: CommandMeta):
        self._command = command

    def parse(self, argv):
        iter_point = 0

        def next_argument():
            nonlocal iter_point
            value = argv[iter_point]
            iter_point += 1
            return value

        def peek_argument():
            nonlocal iter_point
            return argv[iter_point + 1]

        args, kwargs, switches = {}, {}, {}

        while value := next_argument():
            if value is None:
                break

            if value.startswith('--'):
                name = value[2:]

                if name in self._command.kwargs:
                    arg_shape = self._command.get_argument(name)
                    match arg_shape.nargs:
                        case '?':


                elif name in self._command.switches:
                    switches[name] = True
