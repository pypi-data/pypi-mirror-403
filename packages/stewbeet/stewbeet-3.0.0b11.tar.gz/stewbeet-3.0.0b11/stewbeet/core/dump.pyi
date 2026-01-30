from ..utils import get_project_config as get_project_config

def dump_command() -> None:
    """ Handle the 'dump' command to create a zip archive of the project.
    Excludes build outputs, cache directories, and other temporary files.

    Ex: `stewbeet dump [output_name.zip]`
    """
