"""
Predefined values.
"""
try:
    from codename import codename
except ImportError:
    codename = None

APP_NAME = 'Clay Player'
VERSION = '0.6.2'
if codename is not None:
    VERSION_WITH_CODENAME = VERSION + '-' + codename(separator='-', id=VERSION)
else:
    VERSION_WITH_CODENAME = VERSION
USER_AGENT = ' '.join([
    'Mozilla/5.0 (X11; Linux x86_64)'
    'AppleWebKit/537.36 (KHTML, like Gecko)'
    'Chrome/62.0.3202.94 Safari/537.36'
])
