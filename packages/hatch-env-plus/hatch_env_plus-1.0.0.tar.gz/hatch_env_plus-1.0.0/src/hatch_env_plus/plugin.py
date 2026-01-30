import os

from hatchling.version.source.plugin.interface import VersionSourceInterface


class EnvironmentVariableVersionSource(VersionSourceInterface):
    PLUGIN_NAME = 'env-plus'

    def get_version_data(self) -> dict:
        variable = self.config.get('variable', 'PACKAGE_VERSION')
        fallback = self.config.get('fallback', '0.0.0dev0') or None
        version = os.environ.get(variable, fallback)
        return {'version': version}

    def set_version(self, version: str, version_data: dict) -> None:
        version_data['version'] = version
