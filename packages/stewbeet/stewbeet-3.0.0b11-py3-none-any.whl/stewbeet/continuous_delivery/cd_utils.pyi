from ..core.constants import LATEST_MC_VERSION as LATEST_MC_VERSION
from ..utils import ProjectConfig as ProjectConfig, get_project_config as get_project_config
from stouputils import load_credentials as load_credentials

def replace_tilde(path: str) -> str: ...
def get_supported_versions(version: str | list[str] | None = None) -> list[str]:
    ''' Get the supported versions for a given version of Minecraft

\tArgs:
\t\tversion (str): Version of Minecraft
\tReturns:
\t\tlist[str]: List of supported versions, ex: ["1.21.3", "1.21.2"]
\t'''
