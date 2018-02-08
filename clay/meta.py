"""
Predefined values.
"""
APP_NAME = 'Clay Player'
VERSION = '0.7.1'
AUTHOR = "Andrew Dunai"
DESCRIPTION = "Awesome standalone command line player for Google Play Music"

try:
    from codename import codename
except ImportError:
    VERSION_WITH_CODENAME = VERSION
else:
    VERSION_WITH_CODENAME = VERSION + ' (' + codename(separator=' ', id=VERSION) + ')'

COPYRIGHT_MESSAGE = """{app_name} {version}

Copyright 2017 - {year} (C) {author} and {app_name} contributors.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licences/gpl.html>
This is free software; you are free to change it and redistribute it.
There is NO WARRANTY, to the extent permitted by law
""".format(app_name=APP_NAME, year=2018,
           version=VERSION_WITH_CODENAME, author=AUTHOR)

USER_AGENT = ' '.join([
    'Mozilla/5.0 (X11; Linux x86_64)'
    'AppleWebKit/537.36 (KHTML, like Gecko)'
    'Chrome/62.0.3202.94 Safari/537.36'
])
