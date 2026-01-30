import pytest

from hatchling.version.source.plugin.interface import VersionSourceInterface
from hatch_env_plus import EnvironmentVariableVersionSource


def test_plugin_is_version_source():
    assert issubclass(EnvironmentVariableVersionSource, VersionSourceInterface)


def test_plugin_name():
    assert EnvironmentVariableVersionSource.PLUGIN_NAME == 'env-plus'


def test_version_from_env_var():
    """Version is read from environment variable when set."""
    plugin = EnvironmentVariableVersionSource('', {})
    with pytest.MonkeyPatch().context() as m:
        m.setenv('PACKAGE_VERSION', '2.0.0')
        data = plugin.get_version_data()
    assert data == {'version': '2.0.0'}


def test_fallback_when_env_var_not_set():
    """Fallback value is used when environment variable is not set."""
    plugin = EnvironmentVariableVersionSource('', {})
    with pytest.MonkeyPatch().context() as m:
        m.delenv('PACKAGE_VERSION', raising=False)
        data = plugin.get_version_data()
    assert data == {'version': '0.0.0dev0'}


def test_custom_env_var_name():
    """Custom environment variable name is respected."""
    plugin = EnvironmentVariableVersionSource('', {'variable': 'MY_VERSION'})
    with pytest.MonkeyPatch().context() as m:
        m.setenv('MY_VERSION', '3.5.0')
        data = plugin.get_version_data()
    assert data == {'version': '3.5.0'}


def test_custom_fallback_value():
    """Custom fallback value is used when configured."""
    plugin = EnvironmentVariableVersionSource('', {'fallback': '1.0.0'})
    with pytest.MonkeyPatch().context() as m:
        m.delenv('PACKAGE_VERSION', raising=False)
        data = plugin.get_version_data()
    assert data == {'version': '1.0.0'}


def test_env_var_takes_precedence_over_fallback():
    """Environment variable takes precedence over fallback when both are set."""
    plugin = EnvironmentVariableVersionSource(
        '', {'variable': 'CUSTOM_VER', 'fallback': '0.1.0'}
    )
    with pytest.MonkeyPatch().context() as m:
        # Not set - uses fallback
        m.delenv('CUSTOM_VER', raising=False)
        assert plugin.get_version_data() == {'version': '0.1.0'}

        # Set - uses env var
        m.setenv('CUSTOM_VER', '5.0.0')
        assert plugin.get_version_data() == {'version': '5.0.0'}


def test_empty_fallback_string_treated_as_none():
    """Empty fallback string is converted to None."""
    plugin = EnvironmentVariableVersionSource('', {'fallback': ''})
    with pytest.MonkeyPatch().context() as m:
        m.delenv('PACKAGE_VERSION', raising=False)
        data = plugin.get_version_data()
    assert data == {'version': None}
