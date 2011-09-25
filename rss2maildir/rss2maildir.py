# coding=utf-8

# rss2maildir.py - RSS feeds to Maildir 1 email per item
# Copyright (C) 2007  Brett Parker <iDunno@sommitrealweird.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import urllib
import logging

from .Database import Database
from .Feed import Feed
from .Settings import settings
from .utils import make_maildir

log = logging.getLogger('rss2maildir')

def main():
    database = Database(os.path.expanduser(settings['state_dir']))

    for url in settings.feeds():
        if settings.has_option(url, 'name'):
            name = settings.get(url, 'name')
        else:
            name = urllib.urlencode((('', url), )).split("=")[1]

        if settings.has_option(url, 'maildir'):
            relative_maildir = settings.get(url, 'maildir')
        else:
            relative_maildir = settings.get(url, 'maildir_template').replace('{}', name)

        maildir = os.path.join(os.path.expanduser(settings['maildir_root']), relative_maildir)

        try:
            make_maildir(maildir)
        except OSError as e:
            log.warning('Could not create maildir %s: %s' % (maildir, str(e)))
            log.warning('Skipping feed %s' % url)
            continue

        # right - we've got the directories, we've got the url, we know the
        # url... lets play!

        feed = Feed(database, url)
        for item in feed.new_items():
            message = item.create_message(include_html_part = settings.getboolean(feed.url, 'include_html_part'))
            item.deliver(message, maildir)
