from beet import ProjectConfig as ProjectConfig

def get_project_config(directory: str = ...) -> ProjectConfig:
    """ Get the project configuration from the current directory.

    If no configuration file is found, it returns None and prints an error message.

    Args:
        directory (str): The directory to search for the configuration file. Defaults to the current working directory.
    """
