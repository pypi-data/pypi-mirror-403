from .cls.external_item import ExternalItem as ExternalItem
from .cls.item import Item as Item
from beet import Context as Context
from beet.core.utils import JsonDict as JsonDict

class Mem:
    ctx: Context
    definitions: dict[str, JsonDict | Item]
    external_definitions: dict[str, JsonDict | ExternalItem]
