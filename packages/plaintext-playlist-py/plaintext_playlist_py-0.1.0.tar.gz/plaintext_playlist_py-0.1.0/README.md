# plaintext_playlist_py

Library to parse [plaintext-playlist](https://github.com/purarue/plaintext-playlist) files

This is mostly for personal usage, making this installable as a library means I can use it across code/projects/scripts

Also includes some `ID3`/music scripts:

- [`bin/id3stuff`](bin/id3stuff) - a personal opinionated script to set ID3 metadata on `mp3` files using `mutagen` -- prompts me to set the arist/album/album artist for groups of collections by scanning my music directory
- [`bin/linkmusic`](bin/linkmusic) - a `rsync`-like script which creates hardlinks for every file in my playlists into a separate directory (e.g., `~/.local/share/musicsync/`). Then, I use [`syncthing`](https://github.com/syncthing/syncthing) to sync all the songs in my playlists across my computers/onto my phone, without syncing my entire music collection

- [`bin/import-music`](bin/import-music) which calls out to [`beets`](https://beets.io/) and handles fetching metadata/converting/calling `id3stuff` and moving music into my collection. You can see my config for that [here](https://purarue.xyz/d/.config/beets/config.yaml?redirect)

## Installation

Runs on `python3.10+`

To install with pip, run:

    pip install git+https://github.com/purarue/plaintext-playlist

## Usage

`plaintext_playlist_py`

Can run `plaintext_playlist_py list-all` to list all items in playlists

### Tests

```bash
git clone 'https://github.com/purarue/plaintext_playlist_py'
cd ./plaintext_playlist_py
pip install '.[testing]'
flake8 ./plaintext_playlist_py
mypy ./plaintext_playlist_py
```
