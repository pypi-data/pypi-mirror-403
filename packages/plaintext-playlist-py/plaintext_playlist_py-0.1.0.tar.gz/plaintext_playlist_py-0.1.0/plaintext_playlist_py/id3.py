from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError  # type: ignore[import]
from mutagen.easyid3 import EasyID3  # type: ignore[import]

# whether to prompt individually each time
BASIC_TAGS: dict[str, bool] = {
    "title": True,
    "artist": False,
    "album": False,
    "albumartist": False,
}


def safe_id3(f: Path) -> EasyID3:
    try:
        return EasyID3(f)  # type: ignore[no-untyped-call]
    except ID3NoHeaderError:
        # create a empty ID3 frame if nothing exists
        new_data = ID3()  # type: ignore[no-untyped-call]
        new_data.save(f)
        return EasyID3(f)  # type: ignore[no-untyped-call]
