
import click
from my.core.__main__ import _ui_getchar_pick  # from https://github.com/karlicoss/HPI

OTHER = "Other"


def pick_and_or_edit(choices: list[str], prompt: str = "Select from:") -> str:
    """
    Pick from the choices (parts of the Path) to start off with
    then possibly edit the text in your editor to get it to exactly what you want
    """

    ch = list(choices)
    ch.append(OTHER)

    chosen = ch[_ui_getchar_pick(ch, prompt=prompt)]
    if chosen == OTHER:
        chosen = ""

    if chosen == "" or click.confirm(f"Edit {chosen}?", default=False):
        res = click.edit(chosen)
        if res is not None:  # None if no changes made to text
            chosen = res.strip()

    return chosen
