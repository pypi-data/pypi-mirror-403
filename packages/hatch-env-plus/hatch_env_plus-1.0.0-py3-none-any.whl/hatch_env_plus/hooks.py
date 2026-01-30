from hatchling.plugin import hookimpl

from .plugin import EnvironmentVariableVersionSource


@hookimpl
def hatch_register_version_source():
    return EnvironmentVariableVersionSource
