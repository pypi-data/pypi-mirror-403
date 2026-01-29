import configparser
import pathlib
from importlib.metadata import metadata
from importlib.resources import files

import platformdirs

PACKAGE_NAME = metadata(__package__)["Name"]
DESCRIPTION = metadata(PACKAGE_NAME)["Summary"]
VERSION = metadata(PACKAGE_NAME)["Version"]
EPILOG = "🔗 Homepage: https://github.com/eeriemyxi/caicurator"

CONFIG_DIR = pathlib.Path(
    platformdirs.user_config_dir(PACKAGE_NAME, ensure_exists=True)
)

CONFIG_FILE_PATH = CONFIG_DIR / "config.ini"
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_FILE_PATH)

TEMPLATE_PATH = files(f"{PACKAGE_NAME}.assets") / "template.pt"
