from _typeshed import Incomplete
from beet import Context as Context

GENERATION_PLUGINS: Incomplete
FINALYZE_PLUGINS: Incomplete

def beet_default(ctx: Context):
    """ Run all plugins that should run after definitions are loaded.
    This function will yield before finalizing the project (so users can run their own plugins in the middle of the pipeline).

    Requires:
        - StewBeet to be initialized (e.g. from stewbeet.plugins.initialize).
        - Definitions to be loaded
    """
