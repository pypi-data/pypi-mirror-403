import os
import warnings
import subprocess
from typing import NamedTuple, Union
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path


import click


@lru_cache(maxsize=1)
def playlistdir() -> Path:
    proc = subprocess.run(
        ["plainplay", "playlistdir"], check=True, encoding="utf-8", capture_output=True
    )
    p = Path(proc.stdout.strip())
    assert p.exists(), "'plainplay playlistdir' returned path that doesn't exist"
    return p


@lru_cache(maxsize=1)
def musicdir() -> Path:
    return Path(os.environ["PLAINTEXT_PLAYLIST_MUSIC_DIR"])


class PlaylistPath(NamedTuple):
    path: str

    def in_dir(self, directory: Path) -> Path:
        return directory / self.path

    def in_musicdir(self) -> Path:
        return self.in_dir(musicdir())

    def collection_root(self) -> Path:
        return self.in_musicdir().parent


def iterate_playlists(
    playlist_txt_dir: Path | None = None,
    exclude_if_starts_with: list[str] | None = None,
) -> Iterator[PlaylistPath]:
    """
    Get individual lines from each playlist.txt file
    """
    if exclude_if_starts_with is None:
        exclude_if_starts_with = ["_"]
    if playlist_txt_dir is None:
        playlist_txt_dir = playlistdir()

    for playlistfile in playlist_txt_dir.rglob("*.txt"):
        if any(playlistfile.stem.startswith(exc) for exc in exclude_if_starts_with):
            continue
        try:
            for line in filter(
                str.strip, playlistfile.read_text(encoding="utf-8").splitlines()
            ):
                yield PlaylistPath(line.strip())
        except UnicodeDecodeError as e:
            click.echo(f"While decoding {playlistfile}", err=True)
            raise e


class Collection(NamedTuple):
    """
    either an album, a disc of an album or a single
    i.e. some flat collection of mp3 files
    (shouldn't include album art -- that will be searched for later)
    both should be absolute paths
    """

    root: Path
    paths: list[Path]

    @classmethod
    def from_root(
        cls,
        rootdir: Path,
        /,
        ext: str = ".mp3",
    ) -> Union["Collection", None]:
        res = list(cls.iter_ext_collection(rootdir, ext=ext, recursive=False))
        if len(res) == 0:
            warnings.warn(f"Could not find any '{ext}' files in {rootdir}")
            return None
        assert len(res) == 1, f"Expected only one Collection, found {len(res)}"
        return res[0]

    @classmethod
    def iter_ext_collection(
        cls,
        rootdir: Path,
        /,
        *,
        ext: str = ".mp3",
        recursive: bool = True,
    ) -> Iterator["Collection"]:
        """
        Given some directory, return any collections under this
        with a given extension. Defaults to .mp3
        """
        if not ext.startswith("."):
            ext = f".{ext}"
        # if not given a directory, return
        if not rootdir.is_dir():
            return
        paths: list[Path] = []
        for f in map(lambda p: p.absolute(), rootdir.iterdir()):
            if recursive and f.is_dir():
                yield from cls.iter_ext_collection(f, ext=ext, recursive=True)
            elif f.suffix == ext:
                paths.append(f.absolute())
        if len(paths) > 0:
            # sanity check to make sure these are all in the same directory
            assert all(
                [rootdir == pp.parent for pp in paths]
            ), f"Files in multiple directories! {paths}"
            yield cls(root=rootdir.absolute(), paths=paths)


def default_music_dir() -> Path:
    for env_key in ("PLAINTEXT_PLAYLIST_MUSIC_DIR", "XDG_MUSIC_DIR"):
        if env_key in os.environ:
            p = Path(os.environ[env_key])
            if p.exists():
                return p
            else:
                warnings.warn(
                    f"Using default {env_key}, path {os.environ[env_key]} doesn't exist!"
                )
    click.secho(
        "No music dir found in the environment -- set the XDG_MUSIC_DIR environment variable",
        err=True,
        fg="red",
    )
    raise SystemExit(1)
