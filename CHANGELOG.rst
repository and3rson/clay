Changelog
---------

Clay 2.0.0
==========

TBA

* Support the MPRIS2 protocol
* Remove X keybinds and drop the Gtk dependency
* Artist and Album view
* Notification actions
* libmpv support
* Rework of the internals
* Enter appending songs in library or search view
* Dropping of x keybinds
* Add playcount incrementation (by @vale981)
* Fix #37: clay crashing without a running notification daemon (by @agg23)
* Fix #38: no tracks displaying (by @agg3)
* Fix #43: queue doesn't move to the next track (by @agg23)
* Fix #55: Unsafe load() call disabled by Gentoo (by @guitmz)

Clay 1.1.0
==========

2018-08-09

* Liked Songs Playlist
* Thumbs Up / Thumbs Down
* Alphabetical Sorting in Library View
* Explicit Rating Icon
* OSD notifications
* setproctitle to nicely display clay in process list
* Various bugfixes
* Fix #29: customizable tab activation hotkeys
* Fix #31: rating issues

Clay 1.0.0
==========

2018-04-06

 * Configurable keybinds
 * Configurable colors
 * Pluggable X keybinds
 * "My stations" page (by @Fluctuz)
 * Better settings management
 * Equalizer
 * Track caching indicator
 * Optimized settings & cache
 * Code complexity & code climate integration
 * Countless fixes
 * Badges!
 * IRC channel!

Clay 0.7.2
==========

2018-02-12

 * Added --transparent flag

Clay 0.7.1
==========

2018-02-08

 * Late fix for broken setup.py entrypoint support

Clay 0.7.0
==========

2018-02-08

 * Added Dockerfile
 * Fixed installation instructions in README (by Valentijn)
 * Load global hotkeys when X is running only (by Valentijn)
 * Clarified in README that keybinder and pygobject are optional (by Valentijn)
 * Improved error handling and reporting (by Valentijn)
 * Version, help and keybinder command line arguments (by Valentijn)
 * Added copyright (by Valentijn)

Clay 0.6.2
==========

2018-02-02

 * Fixed playback for non-subscribed accounts

Clay 0.6.1
==========

2018-02-02

 * Attempt to fix purchased song while not on paid subscription

Clay 0.6.0
==========

2018-02-01

 * Added track caching option
 * More debugging

Clay 0.5.6
==========

2018-01-31

 * Added debug page

Clay 0.5.5
==========

2018-01-31

 * Added CLAY_DEBUG to log Google Play Music traffic
 * Fixed typo in install_requires
 * Updated README

Clay 0.5.3
==========

2018-01-30

 * Added codename
 * Linter fixes

Clay 0.5.2
==========

2018-01-30

 * Fixed versioning

Clay 0.5.1
==========

2018-01-30

 * Debugging
 * Cleanup & typos
 * Fixed issue with uploaded tracks

Clay 0.5
========

2018-01-29

 * Added slider for eqializer
 * Updated README
 * Misc fixes

Clay 0.4
========
 * Added equalizer

2018-01-29

Clay 0.3
========

2018-01-26

 * Initial functionality
 * Cleanups
 * Notifications
 * Hotkeys
 * Linting
 * Documentation
 * Song search
 * Song context menu
 * Clearer song IDs
 * Auth token caching
 * Colors
 * Copy URL to clipboard
