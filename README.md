- [About](#clay-alpha)
- [Quick start](#quick-start)
- [Documentation](#documentation)
- [Requirements](#requirements)
- [What works](#what-works)
- [What is being developed](#what-is-being-developed)
- [Installation](#installation)
  * [Method 1 (PyPi, automatic)](#method-1-pypi-automatic)
  * [Method 2 (from source, manual)](#method-2-from-source-manual)
  * [Method 3 (in Docker)](#method-3-in-docker)
- [Configuration](#configuration)
- [Controls](#controls)
  * [General](#general)
  * [Songs](#songs)
  * [Playback](#playback)
  * [Equalizer](#equalizer)
  * [Misc](#misc)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)

# Clay [alpha]

[![Build Status](https://travis-ci.org/and3rson/clay.svg?branch=master)](https://travis-ci.org/and3rson/clay) [![Documentation Status](https://readthedocs.org/projects/clay/badge/?version=latest)](http://clay.readthedocs.io/en/latest/?badge=latest)

Standalone command line player for Google Play Music.

This app wouldn't be possible without the wonderful [gmusicapi] and [VLC] libraries.

This project is neither affiliated nor endorsed by Google.

It's being actively developed, but is still in the early alpha version, so many features are missing and/or may be bugged.

(Click the image below to see the screencast.)

[![asciicast](https://asciinema.org/a/69ygwYGRDyB5a7pFgyrwWo1ea.png?1)](https://asciinema.org/a/69ygwYGRDyB5a7pFgyrwWo1ea)

# Quick start

```bash
sudo apt install python-gi python-gi-cairo python3-gi python3-gi-cairo vlc keybinder python-keybinder
pip install --user clay-player
clay
```

# Documentation

Documentation is ![available here](http://clay.readthedocs.io/en/latest/).

# Requirements

- Python 3.x (native)
- [gmusicapi] (PYPI)
- [urwid] (PYPI)
- [PyYAML] (PYPI)
- [PyGObject] (native, optional, used for global X keybinds)
- [Keybinder] (native, optional, used for global X keybinds)
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
- Audio equalizer
- Global hotkeys
- Song file caching
- Configuration UI
- Token caching for faster authorizations
- Song operations (add to library, start station etc.)
- Caching (not for song data, that one is coming soon)
- PYPI package

# What is being developed

- Like/dislike tracks
- Playlist editing
- Artist/album search
- Other functionality that is supported by [gmusicapi]

# Installation

**Warning:** The AUR and PyPy packages called `python3-keybinder` will
not work with Clay since you need to use the official bindings. Since
Ubuntu seperated the official bindings into a different package but
with the same name as the unofficial one it can cause some
confusion. So if you get a `Namespace Keybinder not available` warning
it is probably caused by this. So, for example, on Arch Linux you need
the `libkeybinder3` package instead.

1. Install Python 3, and VLC from your package manager.
2. Optionally, you can install PyGObject, and keybinder plus bindings
   if you want global X keybinds.

## Method 1 (PyPi, automatic)

Just install the player using `pip`:

```bash
pip install --user clay-player
clay
```

## Method 2 (from source, manual)

1. Clone the source code.

2. Create & activate virtualenv with system packages:

    ```bash
    virtualenv --system-site-packages --prompt="(clay) " .env
    source .env/bin/activate
    ```

3. Install the requirements:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the player:

    ```bash
    ./clay/app.py
    ```

## Method 3 (in Docker)

Sometimes you want to run stuff in Docker. You can run Clay in docker as well.

There are two strict requirements:

- You need to build the container by yourself (bacause of PulseAudio related paths & magic cookies.)
- You must have PulseAudio running on host with `module-native-protocol-tcp` module enabled.

Here's how you do it:

1. Clone the source code

2. Create "~/.config/clay" directory (to have proper volume permissions in docker)

    ```bash
    mkdir ~/.config/clay
    ```

3. Build & run the image

    ```bash
    make run
    ```

You *should* get the sound working. Also docker will reuse the Clay config file from host (if you have one).

# Configuration

- Once you launch the app, use the "Settings" page to enter your login and password.
- You will also need to know your Device ID. Thanks to [gmusicapi], the app should display possible IDs once you enter a wrong one.
- Please be aware that this app has not been tested with 2FA yet.
- For people with 2FA, you can just create an app password in Google accounts page and proceed normally. (Thanks @j605)

# Controls

## General

- `<UP|DOWN|LEFT|RIGHT>` - nagivate around
- `<ALT> + 0..9` - switch active tab

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

## Equalizer
- `+` - increase amplification
- `-` - decrease amplification

## Misc

- `<ESC>` or `<CTRL> /` or <CTRL> _ - close most recent notification or popup
- `<CTRL> x` - exit app

## X keybinds
**NOTE:** you need to pass the `--with-x-keybinds` flag for these to work
- `<XF86AudioPlay>` - play/pause the song
- `<XF86AudioNext>` - play the next song
- `<XF86AudioPrev>` - play previous song

# Troubleshooting

At some point, the app may fail. Possible reasons are app bugs,
Google Play Music API issues, [gmusicapi] bugs, [urwid] bugs etc.

If you encounter a problem, please feel free to submit an [issue](https://github.com/and3rson/clay/issues).
I'll try to figure it out ASAP.

Most issues can be reproduced only with specific data coming from Google Play Music servers.

Use "Debug" tab within app to select the error and hit "Enter" to copy it into clipboard.
This will help me to investigate this issue.

# Credits

Made by Andrew Dunai.

Regards to [gmusicapi] and [VLC] who made this possible.

Special thanks to the people who contribute to this project:

- [Valentijn (@ValentijnvdBeek)](https://github.com/ValentijnvdBeek)
- [Sam Kingston (@sjkingo)](https://github.com/sjkingo)

[gmusicapi]: https://github.com/simon-weber/gmusicapi
[VLC]: https://wiki.videolan.org/python_bindings
[urwid]: urwid.org/
[pyyaml]: https://github.com/yaml/pyyaml
[PyGObject]: https://pygobject.readthedocs.io/en/latest/getting_started.html
[Keybinder]: https://github.com/kupferlauncher/keybinder
