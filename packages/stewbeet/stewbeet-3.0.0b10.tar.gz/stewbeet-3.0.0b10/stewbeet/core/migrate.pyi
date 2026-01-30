from ..utils import get_project_config as get_project_config
from typing import Any

def migrate_command() -> None:
    """ Handle the 'migrate' command to migrate an existing datapack/resource pack to StewBeet structure.

    This command will:

    1. Check if there's no existing beet configuration
    2. Search for datapack (data/ folder) and resource pack (assets/ folder)
    3. Download and extract the basic template
    4. Migrate existing files to the src/ folder structure

    Ex: `stewbeet migrate`
    """
def _find_pack_structure(folder_name: str, search_dir: str | None = None) -> dict[str, Any] | None:
    """ Find a pack structure (data/ or assets/) in the current directory or subdirectories.

    Args:
        folder_name: The folder to search for ('data' or 'assets')
        search_dir: Directory to search in (defaults to current working directory)

    Returns:
        A dict with 'path' (str to the folder), 'parent' (parent directory), and 'has_pack_mcmeta' (bool)
        Returns None if not found or if pack.mcmeta doesn't exist alongside
    """
def _migrate_pack(pack_info: dict[str, str | bool], folder_name: str, pack_type: str, working_dir: str) -> None:
    """ Migrate a pack (datapack or resource pack) to the StewBeet structure.

    Args:
        pack_info: Dict containing pack information from _find_pack_structure
        folder_name: 'data' or 'assets'
        pack_type: 'datapack' or 'resource pack' (for logging)
        working_dir: The working directory where migration is happening
    """
