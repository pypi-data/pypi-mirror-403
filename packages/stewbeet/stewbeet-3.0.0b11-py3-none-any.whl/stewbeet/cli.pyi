from .core.dump import dump_command as dump_command
from .core.migrate import migrate_command as migrate_command
from .core.template import template_command as template_command
from .utils import get_project_config as get_project_config
from beet import ProjectConfig as ProjectConfig

def main() -> None: ...
