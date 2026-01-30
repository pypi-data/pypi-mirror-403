import stouputils as stp
from ..__memory__ import Mem as Mem
from ..cls.block import Block as Block, VANILLA_BLOCK_FOR_ORES as VANILLA_BLOCK_FOR_ORES
from ..cls.ingredients import Ingr as Ingr
from ..cls.item import Item as Item
from ..cls.recipe import BlastingRecipe as BlastingRecipe, CraftingShapedRecipe as CraftingShapedRecipe, CraftingShapelessRecipe as CraftingShapelessRecipe, PulverizingRecipe as PulverizingRecipe, SmeltingRecipe as SmeltingRecipe
from ..constants import CUSTOM_BLOCK_VANILLA as CUSTOM_BLOCK_VANILLA, CUSTOM_ITEM_VANILLA as CUSTOM_ITEM_VANILLA
from .equipments import EquipmentsConfig as EquipmentsConfig, SLOTS as SLOTS, VanillaEquipments as VanillaEquipments, format_attributes as format_attributes
from beet.core.utils import JsonDict as JsonDict

@stp.handle_error
def generate_everything_about_this_material(material: str = 'adamantium_fragment', equipments_config: EquipmentsConfig | None = None, ignore_recipes: bool = False) -> None:
    ''' Generate everything related to the ore (armor, tools, weapons, ore, and ingredients (raw, nuggets, blocks)).
\t\tThe function will try to find textures in the assets folder to each item
\t\tAnd return a list of generated items if you want to do something with it.
\tArgs:
\t\tmaterial\t\t\t(str):\t\t\t\t\tThe ore/material to generate everything about (ex: "adamantium_fragment", "steel_ingot", "minecraft:emerald", "minecraft:copper_ingot", "awakened_stardust!")
\t\t\t\t\t\t\t\t\t\t\t\t\tWhen the material ends with "!", the material base will be the material without the "!"
\t\tequipments_config\t(EquipmentsConfig):\tThe base multiplier to apply
\t\tignore_recipes\t(bool):\t\t\t\t\t\tIf True, no recipes will be added in the definitions.
\t'''
def generate_everything_about_these_materials(ores: dict[str, EquipmentsConfig | None], ignore_recipes: bool = False) -> None:
    ''' Uses function \'generate_everything_about_this_material\' for each ore in the ores dictionary.
\tArgs:
\t\tores\t\t(dict[str, EquipmentsConfig|None]):\tThe ores to apply.
\t\t\t\tThe ore/material (key) to generate everything about (ex: "adamantium_fragment", "steel_ingot", "minecraft:emerald", "minecraft:copper_ingot", "awakened_stardust!")
\t\t\t\tWhen the material ends with "!", the material base will be the material without the "!", else we try to cut before the last "_".
\t\tignore_recipes\t(bool):\t\t\t\t\t\tIf True, no recipes will be added in the definitions.
\t'''
def add_recipes_for_dust(material: str, pulverize: list[str | JsonDict], smelt_to: Ingr) -> None:
    ''' Add recipes for dust (pulverize and smelt). If dust isn\'t found in the definitions, it will be added automagically.

\tAll items in the pulverize list will be pulverized to get 2 times the dust.

\tIf the item is a string, their Ingr will be used as "minecraft:{item}"

\tArgs:
\t\tmaterial\t(str):\t\t\t\tThe material to add dust recipes for, ex: "copper" will add recipes for "copper_dust".
\t\tpulverize\t(list[str|dict]):\tThe list of items to pulverize to get 2 times the dust, ex: ["raw_copper", "copper_ore", "deepslate_copper_ore", Ingr("custom_copper", "some_namespace")]
\t\tsmelt_to\t(Ingr):\t\t\t\tThe ingredient representation of the result of smelting the dust, ex: Ingr("minecraft:copper_ingot")}
\t'''
def add_recipes_for_all_dusts(dusts_configs: dict[str, tuple[list[str | JsonDict], Ingr]]) -> None:
    ''' Add recipes for all dusts in the dusts_configs dictionary using the add_recipes_for_dust function.

\tArgs:
\t\tdusts_configs\t(dict[str, tuple[list[str|dict],dict]]):\tThe dusts to add recipes for, ex:

\t```py
\t{
\t\t"copper": (
\t\t\t["raw_copper", "copper_ore", "deepslate_copper_ore", Ingr("custom_copper", "some_namespace")],
\t\t\tIngr("minecraft:copper_ingot")
\t\t)
\t}
\t```
\t'''
