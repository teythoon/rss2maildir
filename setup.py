#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'rss2maildir',
    version = '0.1',
    description = 'rss2maildir takes rss feeds and creates a maildir of messages for each of the feeds',
    url = 'https://github.com/teythoon/rss2maildir',
    packages = ['rss2maildir'],
    package_data = {'rss2maildir': ['defaults/rss2maildir.conf']},
    scripts = ['bin/rss2maildir'],
)
