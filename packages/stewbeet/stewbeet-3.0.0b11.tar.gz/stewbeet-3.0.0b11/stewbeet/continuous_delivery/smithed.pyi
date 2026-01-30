from .cd_utils import get_supported_versions as get_supported_versions
from beet.core.utils import JsonDict as JsonDict

SMITHED_API_URL: str

def validate_credentials(credentials: JsonDict) -> tuple[str, str]:
    """ Get and validate Smithed credentials

\tArgs:
\t\tcredentials (dict[str, str]): Credentials for the Smithed API
\tReturns:
\t\tstr: API key for Smithed
\t\tstr: GitHub author
\t"""
def validate_config(smithed_config: dict[str, str]) -> tuple[str, str, str]:
    """ Validate Smithed configuration

\tArgs:
\t\tsmithed_config (dict[str, str]): Configuration for the Smithed project
\tReturns:
\t\tstr: Project name on Smithed
\t\tstr: Version of the project
\t\tstr: Slug (namespace) of the project
\t"""
def upload_version(project_id: str, project_name: str, version: str, api_key: str, author: str) -> None:
    """ Upload new version

\tArgs:
\t\tproject_id\t\t(str):\t\t\t\tSmithed project ID
\t\tproject_name\t(str):\t\t\t\tName of the project
\t\tversion\t\t\t(str):\t\t\t\tVersion number
\t\tapi_key\t\t\t(str):\t\t\t\tAPI key for Smithed
\t\tauthor\t\t\t(str):\t\t\t\tAuthor (for the github link)
\t"""
def upload_to_smithed(credentials: dict[str, str], smithed_config: dict[str, str], changelog: str = '') -> None:
    """ Upload the project to Smithed using the credentials and the configuration

\tArgs:
\t\tcredentials\t\t(dict[str, str]):\tCredentials for the Smithed API
\t\tsmithed_config\t(dict[str, str]):\tConfiguration for the Smithed project
\t\tchangelog\t\t(str):\t\t\t\tChangelog text for the release
\t"""
