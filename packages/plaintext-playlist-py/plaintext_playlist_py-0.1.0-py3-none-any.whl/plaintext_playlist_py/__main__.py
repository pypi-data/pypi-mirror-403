import click


@click.group()
def main() -> None:
    """plaintext-playlist python library"""


@main.command(short_help="list all songs in playlists")
def list_all() -> None:
    """
    List the absolute paths of all music files in the playlist dir
    """
    from . import iterate_playlists

    for f in iterate_playlists():
        click.echo(f.in_musicdir())


if __name__ == "__main__":
    main(prog_name="plaintext_playlist_py")
