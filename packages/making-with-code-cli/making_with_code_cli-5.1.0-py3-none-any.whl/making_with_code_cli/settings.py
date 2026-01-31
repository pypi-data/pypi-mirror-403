from pathlib import Path
import tomlkit
import os


def get_settings_path(settings_path=None):
    """Determines the settings path, based on what is passed and environment.
    "The default location for the MWC configuration file is ~/.mwc.
    This can be specified (e.g. to support parallel installations) using
    the MWC_CONFIG environment variable or the --config flag.
    """
    if settings_path:
        return Path(settings_path)
    elif "MWC_CONFIG" in os.environ:
        return Path(os.environ["MWC_CONFIG"])
    else:
        xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return xdg_config_home / "mwc" / "settings.toml"

def read_settings(settings_path=None):
    """Reads the settings file and returns a dict. 
    If the settings file does not exist, returns {}
    """
    sp = get_settings_path(settings_path)
    if sp.exists():
        with open(sp, "rb") as f:
            return tomlkit.load(f)
    else:
        return {}

def iter_settings(settings, prefix=None):
    """Iterates through the settings dict, yielding (key, value) pairs.
    Nested keys are returned with dots: {'a': {'b': 'c'}} -> ('a.b', 'c')
    """
    for key, value in settings.items():
        keypath = (prefix or []) + [key]
        if isinstance(value, dict):
            for k, v in _iter_settings(value, prefix=keypath):
                yield '.'.join(keypath), v
        else:
            yield '.'.join(keypath), value

# TODO
def check_settings(settings):
    """Checks that all settings match SETTINGS_FORMAT"""
    errors = []

def write_settings(settings, settings_path=None):
    """Writes the settings to the settings file."""
    sp = get_settings_path(settings_path)
    with open(sp, "w") as f:
        tomlkit.dump(settings, f)
