import stouputils as stp
from ..__memory__ import Mem as Mem
from beet.core.utils import JsonDict as JsonDict
from enum import Enum

SLOTS: dict[str, str]
UNIQUE_SLOTS_VALUES: list[str]

class DefaultOre(Enum):
    NETHERITE = 'netherite'
    DIAMOND = 'diamond'
    IRON = 'iron'
    GOLD = 'golden'
    CHAINMAIL = 'stone'
    COPPER = 'copper'
    LEATHER = 'wooden'

class VanillaEquipments(Enum):
    """ Default vanilla equipments values (durability, armor, armor_toughness, knockback_resistance, attack_damage, attack_speed) """
    HELMET = ...
    CHESTPLATE = ...
    LEGGINGS = ...
    BOOTS = ...
    SWORD = ...
    PICKAXE = ...
    AXE = ...
    SHOVEL = ...
    HOE = ...
    SPEAR = ...

class EquipmentsConfig:
    ignore_recipes: bool
    equivalent_to: DefaultOre
    pickaxe_durability: int
    attributes: dict[str, float]
    def __init__(self, equivalent_to: DefaultOre = ..., pickaxe_durability: float | int = 0, attributes: dict[str, float] | None = None, ignore_recipes: bool = False) -> None:
        ''' Creates a configuration for equipments (based on the pickaxe)

\t\tArgs:
\t\t\tequivalent_to (DEFAULT_ORE):\tThe equivalent ore to compare to (ex: DEFAULT_ORE.DIAMOND)
\t\t\tpickaxe_durability (int):\t\tThe pickaxe durability that will be used to calculate the durability of other equipments
\t\t\tattributes (dict[str, float]):\t(optional) Attributes with type "add_value" to add (not override) to the equipment (ex: "attack_damage": 1.0, means 6 attack damage for diamond pickaxe)
\t\t\t\t{"attack_damage": 1.0, "armor": 1.0, "mining_efficiency": 1}
\t\t\t\tattack_damage and mining_efficiency are always on tools
\t\t\t\tarmor and armor_toughness is always on armor
\t\t\tignore_recipes (bool):\t\t\tWhether to ignore recipes generation for this material or not

\t\tIf you need a specific attribute for a generated item, you should append it afterward.
\t\t'''
    def getter(self) -> tuple[DefaultOre, int, dict[str, float]]: ...
    @stp.simple_cache
    def get_tools_attributes(self) -> dict[str, float]: ...
    @stp.simple_cache
    def get_armor_attributes(self) -> dict[str, float]: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

def format_attributes(attributes: dict[str, float], slot: str, attr_config: dict[str, float] | None = None) -> list[JsonDict]:
    """ Returns generated attribute_modifiers key for an item (adds up attributes and config) """
