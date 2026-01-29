"""
To be used with `hpi query`

more info

https://github.com/purarue/ttally/blob/master/ttally/__main__.py
https://github.com/karlicoss/HPI#which-month-in-2020-did-i-make-the-most-git-commits-in
"""

import typing as t
from pathlib import Path

from . import Collection, musicdir


def collections() -> t.Iterator[Collection]:
    yield from Collection.iter_ext_collection(musicdir())


def songs() -> t.Iterator[Path]:
    from . import iterate_playlists

    yield from map(lambda p: p.in_musicdir(), iterate_playlists())
