import stouputils as stp
from .cd_utils import get_supported_versions as get_supported_versions
from beet.core.utils import JsonDict as JsonDict

MODRINTH_API_URL: str
PROJECT_ENDPOINT: str
VERSION_ENDPOINT: str

def validate_credentials(credentials: dict[str, str]) -> str:
    """ Get and validate Modrinth credentials

\tArgs:
\t\tcredentials (dict[str, str]): Credentials for the Modrinth API
\tReturns:
\t\tstr: API key for Modrinth
\t"""
def validate_config(modrinth_config: JsonDict) -> tuple[str, str, str, str, str, str, str]:
    """ Validate Modrinth configuration

\tArgs:
\t\tmodrinth_config (JsonDict): Configuration for the Modrinth project
\tReturns:
\t\tstr: Project name on Modrinth
\t\tstr: Version of the project
\t\tstr: Slug (namespace) of the project
\t\tstr: Summary of the project
\t\tstr: Description in Markdown format
\t\tstr: Version type (release, beta, alpha)
\t\tstr: Build folder path
\t"""
def get_project(slug: str, headers: dict[str, str]) -> dict[str, str]:
    """ Get project from Modrinth

\tArgs:
\t\tslug (str): Project slug/namespace
\t\theaders (dict[str, str]): Headers for Modrinth API requests
\tReturns:
\t\tdict: Project data
\t"""
def update_project_description(slug: str, description: str, summary: str, headers: dict[str, str]) -> None:
    """ Update project description and summary

\tArgs:
\t\tslug (str): Project slug/namespace
\t\tdescription (str): Project description in Markdown
\t\tsummary (str): Project summary
\t\theaders (dict[str, str]): Headers for Modrinth API requests
\t"""
def handle_existing_version(slug: str, version: str, headers: dict[str, str]) -> bool:
    """ Check and handle existing version

\tArgs:
\t\tslug (str): Project slug/namespace
\t\tversion (str): Version to check
\t\theaders (dict[str, str]): Headers for Modrinth API requests
\tReturns:
\t\tbool: True if we should continue, False otherwise
\t"""
def generate_fabric_metadata(mod_id: str, metadata: JsonDict) -> str:
    """ Generate Fabric mod metadata JSON

\tArgs:
\t\tmod_id (str): Mod ID
\t\tmetadata (dict): Mod metadata
\tReturns:
\t\tstr: Fabric mod.json content
\t"""
def generate_forge_metadata(mod_id: str, metadata: JsonDict, is_neoforge: bool = False) -> str:
    """ Generate Forge/NeoForge mod metadata TOML

\tArgs:
\t\tmod_id (str): Mod ID
\t\tmetadata (dict): Mod metadata
\t\tis_neoforge (bool): Whether this is for NeoForge (uses javafml) or Forge (uses lowcodefml)
\tReturns:
\t\tstr: mods.toml content
\t"""
def generate_quilt_metadata(mod_id: str, metadata: JsonDict) -> str:
    """ Generate Quilt mod metadata JSON

\tArgs:
\t\tmod_id (str): Mod ID
\t\tmetadata (dict): Mod metadata
\tReturns:
\t\tstr: quilt.mod.json content
\t"""
def convert_datapack_to_mod(datapack_path: str, output_path: str, metadata: JsonDict, platforms: list[str], resource_pack_path: str | None = None) -> None:
    """ Convert a datapack ZIP to a mod JAR with proper metadata files

\tArgs:
\t\tdatapack_path (str): Path to the datapack ZIP file
\t\toutput_path (str): Path where to save the mod JAR file
\t\tmetadata (dict): Mod metadata (id, name, version, description, authors, etc.)
\t\tplatforms (list[str]): List of platforms (fabric, forge, neoforge, quilt)
\t\tresource_pack_path (str): Optional path to the resource pack ZIP file
\t"""
def get_file_parts(project_name: str, build_folder: str, modrinth_config: JsonDict, project_data: JsonDict | None = None) -> list[str]:
    """ Get file parts to upload

\tArgs:
\t\tproject_name (str): Name of the project
\t\tbuild_folder (str): Path to build folder
\t\tmodrinth_config (dict): Modrinth configuration
\t\tproject_data (dict): Optional project data from Modrinth API
\tReturns:
\t\tlist[str]: List of file paths to upload
\t"""
def upload_version(project_id: str, project_name: str, version: str, version_type: str, changelog: str, file_parts: list[str], headers: dict[str, str], dependencies: list[str] | None = None, loaders: list[str] | None = None) -> JsonDict:
    """ Upload new version

\tArgs:
\t\tproject_id\t\t(str):\t\t\t\tModrinth project ID
\t\tproject_name\t(str):\t\t\t\tName of the project
\t\tversion\t\t\t(str):\t\t\t\tVersion number
\t\tversion_type\t(str):\t\t\t\tType of version (release, beta, alpha)
\t\tchangelog\t\t(str):\t\t\t\tChangelog text
\t\tfile_parts\t\t(list[str]):\t\tList of files to upload
\t\theaders\t\t\t(dict[str, str]):\tHeaders for Modrinth API requests
\t\tdependencies\t(list[str]):\t\tList of dependencies
\t\tloaders\t\t\t(list[str]):\t\tList of loaders (datapack, fabric, forge, etc.)
\tReturns:
\t\tdict: Upload response data
\t"""
def set_resource_pack_required(version_id: str, resource_pack_hash: str, headers: dict[str, str]) -> None:
    """ Set resource pack as required

\tArgs:
\t\tversion_id (str): ID of the version
\t\tresource_pack_hash (str): SHA1 hash of resource pack
\t\theaders (dict[str, str]): Headers for Modrinth API requests
\t"""
@stp.handle_error
def upload_to_modrinth(credentials: dict[str, str], modrinth_config: JsonDict, changelog: str = '') -> None:
    """ Upload the project to Modrinth using the credentials and the configuration

\tArgs:
\t\tcredentials\t\t(dict[str, str]):\tCredentials for the Modrinth API
\t\tmodrinth_config\t(dict):\t\t\t\tConfiguration for the Modrinth project
\t\tchangelog\t\t(str):\t\t\t\tChangelog text for the release
\t"""
