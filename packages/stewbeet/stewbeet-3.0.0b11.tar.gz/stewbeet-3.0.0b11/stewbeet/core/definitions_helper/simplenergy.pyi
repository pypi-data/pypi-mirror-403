from ..__memory__ import Mem as Mem
from ..cls.item import Item as Item
from beet.core.utils import TextComponent as TextComponent

def format_energy_number(number: int) -> str:
    ''' Formats a number into a string with appropriate unit suffix (k, M, G, T).

\tArgs:
\t\tnumber (int): The number to format
\tReturns:
\t\tstr: Formatted string with unit suffix, ex: 12000 -> "12 M", 1200 -> "1200 k"
\t'''
def create_energy_lore(energy_data: dict[str, int]) -> TextComponent:
    """ Creates lore entries for energy-related blocks based on their energy data.

\tArgs:
\t\tenergy_data (dict): Dictionary containing energy configuration values
\tReturns:
\t\tTextComponent: Formatted text component with energy lore
\t"""
def add_energy_lore_to_definitions() -> None:
    """ Adds energy-related lore to definitions based on their custom data. """
