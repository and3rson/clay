# Clay [alpha]

[![Build Status](https://travis-ci.org/and3rson/clay.svg?branch=master)](https://travis-ci.org/and3rson/clay) [![Documentation Status](https://readthedocs.org/projects/clay/badge/?version=latest)](http://clay.readthedocs.io/en/latest/?badge=latest)

Standalone command line player for Google Play Music.

This app wouldn't be possible without the wonderful [gmusicapi] and [VLC] libraries.

This project is neither affiliated nor endorsed by Google.

It's being actively developed, but is still in the early alpha version, so many features are missing and/or may be bugged.

(Click the image below to see the screencast.)

[![asciicast](https://asciinema.org/a/69ygwYGRDyB5a7pFgyrwWo1ea.png?1)](https://asciinema.org/a/69ygwYGRDyB5a7pFgyrwWo1ea)

# Installation

```bash
sudo pip install clay-player
clay
```

# Documentation

Documentation is ![available here](http://clay.readthedocs.io/en/latest/).

# Requirements

- Python 3.x (native)
- [gmusicapi] (PYPI)
- [urwid] (PYPI)
- [PyYAML] (PYPI)
- lib[VLC] (native, distributed with VLC player)

# What works
- Playback
- Music library browsing & management
- Playlists
- Radio stations
- Song search
- Filtering results
- Queue management
- Notifications
- Global hotkeys
- Configuration UI
- Token caching for faster authorizations
- Song operations (add to library, start station etc.)
- Caching (not for song data, that one is coming soon)

# What is being developed

- Like/dislike tracks
- Playlist editing
- Artist/album search
- Other functionality that is supported by [gmusicapi]
- PYPI package

# Installation

0. Install Python 3 and VLC.

## Method 1 (automatic)

1. Source the 'activate.sh' script. It will initialize the Python virtual env and install the dependencies:

    ```bash
    source activate.sh
    ```

2. Run the player:

    ```bash
    ./clay/app.py
    ```

## Method 2 (manual)

1. Create & activate virtualenv:

    ```bash
    virtualenv .env
    source .env/bin/activate
    ```

2. Install the requirements:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the player:

    ```bash
    ./clay/app.py
    ```

# Configuration

In order to use this app, you need to know your Device ID. Typically gmusicapi should display possible IDs once you type a wrong one.
Also be aware that this app has not been tested with 2FA yet.

# Controls

## General

- `<UP|DOWN|LEFT|RIGHT>` - nagivate around
- `<ALT> + 1..9` - switch active tab

## Songs

- `<ENTER>` - play highlighted track
- `<CTRL> w` - play/pause
- `<CTRL> e` - play next song
- `<CTRL> a` - append highlighted song to the queue
- `<CTRL> u` - remove highlighted song from the queue
- `<CTRL> p` - start station from highlighted song
- `<ALT> m` - show context menu for this song

## Playback

- `<CTRL> s` - toggle shuffle
- `<CTRL> r` - toggle song repeat
- `<SHIFT> <LEFT|RIGHT>` - seek backward/forward by 5% of the song duration
- `<CTRL> q` - seek to song beginning

## Misc

- `<ESC>` or `<CTRL> /` or <CTRL> _ - close most recent notification
- `<CTRL> x` - exit app

# Credits

Made by Andrew Dunai.

Regards to [gmusicapi] and [VLC] who made this possible.

[gmusicapi]: https://github.com/simon-weber/gmusicapi
[VLC]: https://wiki.videolan.org/python_bindings
[urwid]: urwid.org/
[pyyaml]: https://github.com/yaml/pyyaml

