from beet.core.utils import JsonDict as JsonDict

def create_gradient_text(text: str, start_hex: str = 'c24a17', end_hex: str = 'c77e36', text_length: int | None = None) -> list[JsonDict]:
    """ Create a gradient text effect by interpolating colors between start and end hex.

\tArgs:
\t\ttext        (str): The text to apply the gradient to.
\t\tstart_hex   (str): Starting color in hex format (e.g. 'c24a17').
\t\tend_hex     (str): Ending color in hex format (e.g. 'c77e36').
\t\ttext_length (int | None): Optional length override for the text. If provided, uses this instead of len(text).

\tReturns:
\t\tlist[JsonDict]: List of text components, each with a letter and its color.
\t"""
def rainbow_gradient_text(text: str) -> list[JsonDict]:
    """ Create a rainbow gradient text effect that cycles through the color spectrum from red to red.

\tArgs:
\t\ttext (str): The text to apply the rainbow gradient to.

\tReturns:
\t\tlist[JsonDict]: List of text components, each with a letter and its rainbow color.
\t"""
def gradient_text_to_string(gradient_text: list[JsonDict], color_pos: int = 0) -> dict[str, str]:
    """ Convert a gradient text back to a string, optionally getting the color at a specific position.

\tArgs:
\t\tgradient_text (list[JsonDict]):  The gradient text to convert back to a string.
\t\tcolor_pos     (int):                   The position to get the color from.

\tReturns:
\t\tdict[str, str]: A dictionary containing the concatenated text and its color at the specified position.
\t"""
