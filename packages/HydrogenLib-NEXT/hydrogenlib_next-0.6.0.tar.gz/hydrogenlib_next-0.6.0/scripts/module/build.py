import dataclasses
import os
import shutil
import sys
from pathlib import Path

from packaging.version import Version

from scripts.base import Project, console, Module

special_version_strings = {"patch", 'major', 'minor'}


@dataclasses.dataclass
class BuildConfig:
    name: str
    version: str | None | Version
    path: os.PathLike[str]


def parse_build_config(arg: str):
    if "==" in arg:
        name, ver = arg.split("==")
        if ver in special_version_strings:
            return name.lower(), ver

        return name.lower(), Version(ver)

    else:
        return arg.lower(), None


def reset_version(module: Module, ver: str):
    name = module.name
    current_ver = module.version
    if ver not in special_version_strings:
        if current_ver > ver:
            raise RuntimeError(f"Module [bold]{name}[/bold]: You cannot be downgraded")
    else:
        module.version = ver


def main():
    project = Project.find()

    builds = sys.argv[1::]

    vaild_modules = []

    for build_string in builds:
        name, ver = parse_build_config(build_string)
        module = project.find_module(name)
        vaild_modules.append((module, ver))
        console.info(f'Getting module [bold]{name}[/bold] ({module.version})')

    for module, ver in vaild_modules:
        if ver:
            with console.status(f'Setting version for [bold]{module.name}[/bold]'):
                reset_version(module, ver)
            console.print(f'Module {module.name} is {module.version}')

        with console.status(f'Building [bold]{module.name}[/bold]'):
            module.build()


if __name__ == "__main__":
    main()
