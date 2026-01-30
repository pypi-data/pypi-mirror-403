from ..dependencies.bookshelf import BOOKSHELF_MODULES as BOOKSHELF_MODULES
from beet.core.utils import JsonDict as JsonDict
from beet.toolchain.config import FormatSpecifier as FormatSpecifier

MORE_DATA_PACK_FORMATS: dict[tuple[int, ...], FormatSpecifier]
MORE_ASSETS_PACK_FORMATS: dict[tuple[int, ...], FormatSpecifier]
MORE_DATA_VERSIONS: dict[tuple[int, ...], int]
LATEST_MC_VERSION: str
CATEGORY: str
CUSTOM_BLOCK_VANILLA: str
CUSTOM_BLOCK_ALTERNATIVE: str
CUSTOM_BLOCK_HEAD: str
CUSTOM_ITEM_VANILLA: str
VANILLA_BLOCK: str
NO_SILK_TOUCH_DROP: str
OVERRIDE_MODEL: str
SMITHED_CRAFTER_COMMAND: str
PAINTING_DATA: str
GROWING_SEED: str
WIKI_COMPONENT: str
RESULT_OF_CRAFTING: str
USED_FOR_CRAFTING: str
NOT_COMPONENTS: list[str]
COMMON_SIGNAL: str
COMMON_SIGNAL_HIDDEN: str
FACES: tuple[str, ...]
SIDES: tuple[str, ...]
DOWNLOAD_VANILLA_ASSETS_RAW: str
DOWNLOAD_VANILLA_ASSETS_SPECIAL_RAW: str
DOWNLOAD_VANILLA_ASSETS_SOURCE: str
CUSTOM_BLOCK_HEAD_CUBE_RADIUS: tuple[int, int, int]
BLOCKS_WITH_INTERFACES: list[str]

class Conventions:
    """ Defines conventions for tags used in datapacks. """
    NO_KILL_TAGS: list[str]
    ENTITY_TAGS: list[str]
    BLOCK_TAGS: list[str]
    ENTITY_TAGS_NO_KILL: list[str]
    BLOCK_TAGS_NO_KILL: list[str]
    AVOID_NO_KILL: str
    AVOID_ENTITY_TAGS: str
    AVOID_BLOCK_TAGS: str
    AVOID_ENTITY_TAGS_NO_KILL: str
    AVOID_BLOCK_TAGS_NO_KILL: str

def official_lib_used(lib: str) -> bool: ...

OFFICIAL_LIBS: dict[str, JsonDict]
