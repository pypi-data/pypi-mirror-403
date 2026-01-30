from ..__memory__ import Mem as Mem
from ..cls.external_item import ExternalItem as ExternalItem
from ..cls.item import Item as Item
from ..utils.io import convert_to_serializable as convert_to_serializable

def add_item_model_component(black_list: list[str] | None = None) -> None:
    """ Add an item model component to all items in the definitions.

\tArgs:
\t\tblack_list\t\t\t(list[str]):\tThe list of items to ignore.
\t\tignore_paintings\t(bool):\t\t\tWhether to ignore items that are paintings (have PAINTING_DATA).
\t"""
def add_item_name_and_lore_if_missing(is_external: bool = False, black_list: list[str] | None = None) -> None:
    """ Add item name and lore to all items in the definitions if they are missing.

\tArgs:
\t\tis_external\t(bool):\t\t\t\tWhether the definitions is the external one or not (meaning the namespace is in the item name).
\t\tblack_list\t(list[str]):\t\tThe list of items to ignore.
\t"""
def add_private_custom_data_for_namespace(is_external: bool = False, black_list: list[str] | None = None) -> None:
    """ Add private custom data for namespace to all items in the definitions if they are missing.

\tArgs:
\t\tis_external\t(bool):\t\t\t\tWhether the definitions is the external one or not (meaning the namespace is in the item name).
\t\tblack_list\t(list[str]):\t\tThe list of items to ignore.
\t"""
def add_smithed_ignore_vanilla_behaviours_convention() -> None:
    """ Add smithed convention to all items in the definitions if they are missing.

\tRefer to https://wiki.smithed.dev/conventions/tag-specification/#custom-items for more information.
\t"""
def set_manual_components(white_list: list[str]) -> None:
    """ Override the components to include in the manual when hovering items.

\tArgs:
\t\twhite_list\t(list[str]):\tThe list of components to include.
\t"""
def export_all_definitions_to_json(file_name: str, is_external: bool = False, verbose: bool = True) -> None:
    """ Export all definitions to a single json file for debugging purposes.

\tArgs:
\t\tfile_name\t(str):\tThe name of the file to export to.
\t\tis_external\t(bool):\tWhether to export external definitions or not.
\t\tverbose\t\t(bool):\tWhether to print a debug message or not.
\t"""
