TEMPLATES_URL: dict[str, dict[str, str]]

def template_command() -> None:
    """ Handle the 'init/template' command to create a new project from a template.
    If no template name is provided, it asks the user to choose one.

    Ex: `stewbeet init [template_name]`
    """
