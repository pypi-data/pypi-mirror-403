from ..__memory__ import Mem as Mem
from ..cls.item import Item as Item
from ..utils.sounds import add_sound as add_sound
from beet.core.utils import JsonDict as JsonDict

def clean_record_name(name: str) -> str:
    """ Clean a record name by removing special characters and converting to lowercase.

\tArgs:
\t\tname (str): The name to clean

\tReturns:
\t\tstr: The cleaned name containing only lowercase letters, numbers and underscores
\t"""
def generate_custom_records(records: dict[str, str] | str | None = 'auto', category: str | None = None) -> None:
    ''' Generate custom records by searching in assets/records/ for the files and copying them to the definitions and resource pack folder.

\tArgs:
\t\tdefinitions\t(dict[str, dict]):\tThe definitions to add the custom records items to, ex: {"record_1": "song.ogg", "record_2": "another_song.ogg"}
\t\trecords\t\t(dict[str, str]):\tThe custom records to apply, ex: {"record_1": "My first Record.ogg", "record_2": "A second one.ogg"}
\t\tcategory\t(str):\t\t\t\tThe definitions category to apply to the custom records (ex: "music").
\t'''
