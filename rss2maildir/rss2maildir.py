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

import sys
import os
import stat
import logging
import urllib

import feedparser

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

import datetime
import random
import string

import socket

from base64 import b64encode

if sys.version_info[0] == 2 and sys.version_info[1] >= 6:
    import hashlib as md5
else:
    import md5

import cgi

import re

from .HTML2Text import HTML2Text
from .utils import make_maildir, open_url

log = logging.getLogger('rss2maildir')

serialize = urllib.urlencode
deserialize = lambda data: dict((key, value[0]) for key, value in cgi.parse_qs(data).items())

class Item(object):
    def __init__(self, feed, feed_item):
        self.feed = feed

        self.author = feed_item.get('author', self.feed.url)
        self.title = feed_item['title']
        self.link = feed_item['link']

        if feed_item.has_key('content'):
            self.content = feed_item['content'][0]['value']
        else:
            if feed_item.has_key('description'):
                self.content = feed_item['description']
            else:
                self.content = u''

        self.md5sum = md5.md5(self.content.encode('utf-8')).hexdigest()
        self.prevmessageid = None

        self.guid = feed_item.get('guid', None)
        if self.guid:
            self.db_guid_key = (self.feed.url + u'|' + self.guid).encode('utf-8')
        else:
            self.db_guid_key = None

        self.db_link_key = (self.feed.url + u'|' + feed_item['link']).encode('utf-8')

        self.createddate = datetime.datetime.now().strftime('%a, %e %b %Y %T -0000')
        updated_parsed = feed_item['updated_parsed'][0:6]
        try:
            self.createddate = datetime.datetime(*updated_parsed) \
                .strftime('%a, %e %b %Y %T -0000')
        except TypeError as e:
            log.warning('Parsing date %s failed: %s' % (updated_parsed, str(e)))


    def seen_before(self):
        if self.db_guid_key:
            if self.feed.database.seen.has_key(self.db_guid_key):
                data = deserialize(self.feed.database.seen[self.db_guid_key])
                if data['contentmd5'] == self.md5sum:
                    return True

        if self.feed.database.seen.has_key(self.db_link_key):
            data = deserialize(self.feed.database.seen[self.db_link_key])

            if data.has_key('message-id'):
                self.prevmessageid = data['message-id']

            if data['contentmd5'] == self.md5sum:
                return True

        return False

class Feed(object):
    def __init__(self, database, url):
        self.database = database
        self.url = url
        self.name = url

    def is_changed(self):
        if not self.database.feeds.has_key(self.url):
            return True

        previous_data = cgi.parse_qs(self.database.feeds[self.url])

        response = open_url("HEAD", self.url)
        if not response:
            log.warning('Fetching feed %s failed' % self.name)
            return True

        result = False
        for key, value in response.getheaders():
            if previous_data.get(key, None) != value:
                result = True
                break

        return result

    def parse_and_deliver(self, maildir):
        if not self.is_changed():
            return

        response = open_url("GET", self.url)
        if not response:
            log.warning('Fetching feed %s failed' % (self.url))
            return

        headers = response.getheaders()
        feedhandle = response

        fp = feedparser.parse(feedhandle)
        for item in (Item(self, feed_item) for feed_item in fp["items"]):
            if item.seen_before():
                continue

            # create a basic email message
            msg = MIMEMultipart("alternative")
            messageid = "<" \
                + datetime.datetime.now().strftime("%Y%m%d%H%M") \
                + "." \
                + "".join( \
                    [random.choice( \
                        string.ascii_letters + string.digits \
                        ) for a in range(0,6) \
                    ]) + "@" + socket.gethostname() + ">"
            msg.add_header("Message-ID", messageid)
            msg.set_unixfrom("\"%s\" <rss2maildir@localhost>" %(self.url))
            msg.add_header("From", "\"%s\" <rss2maildir@localhost>" % (item.author))
            msg.add_header("To", "\"%s\" <rss2maildir@localhost>" %(self.url))
            if item.prevmessageid:
                msg.add_header("References", item.prevmessageid)
            msg.add_header("Date", item.createddate)
            msg.add_header("X-rss2maildir-rundate", datetime.datetime.now() \
                .strftime("%a, %e %b %Y %T -0000"))
            subj_gen = HTML2Text()

            title = item.title.replace(u'<', u'&lt;').replace(u'>', u'&gt;')
            subj_gen.feed(title.encode("utf-8"))
            msg.add_header("Subject", subj_gen.gettext())
            msg.set_default_type("text/plain")

            htmlcontent = "%s\n\n<p>Item URL: <a href='%s'>%s</a></p>" % (
                item.content,
                item.link,
                item.link
            )
            htmlpart = MIMEText(htmlcontent.encode("utf-8"), "html", "utf-8")
            textparser = HTML2Text()
            textparser.feed(item.content.encode("utf-8"))
            textcontent = "%s\n\nItem URL: %s" % (
                textparser.gettext(),
                item.link
            )
            textpart = MIMEText(textcontent.encode("utf-8"), "plain", "utf-8")
            msg.attach(textpart)
            msg.attach(htmlpart)

            # start by working out the filename we should be writting to, we do
            # this following the normal maildir style rules
            fname = str(os.getpid()) \
                + "." + socket.gethostname() \
                + "." + "".join( \
                    [random.choice( \
                        string.ascii_letters + string.digits \
                        ) for a in range(0,10) \
                    ]) + "." \
                + datetime.datetime.now().strftime('%s')
            fn = os.path.join(maildir, "tmp", fname)
            fh = open(fn, "w")
            fh.write(msg.as_string())
            fh.close()
            # now move it in to the new directory
            newfn = os.path.join(maildir, "new", fname)
            os.link(fn, newfn)
            os.unlink(fn)

            # now add to the database about the item
            if item.prevmessageid:
                messageid = item.prevmessageid + " " + messageid

            data = serialize({
                'message-id': messageid,
                'created': item.createddate,
                'contentmd5': item.md5sum
            })

            if item.guid and item.guid != item.link:
                self.database.seen[item.db_guid_key] = data
                try:
                    previous_data = deserialize(self.database.seen[item.db_link_key])
                    newdata = serialize({
                        'message-id': messageid,
                        'created': previous_data['created'],
                        'contentmd5': previous_data['contentmd5']
                    })
                    self.database.seen[item.db_link_key] = newdata
                except:
                    self.database.seen[item.db_link_key] = data
            else:
                self.database.seen[item.db_link_key] = data

        if headers:
            data = []
            for header in headers:
                if header[0] in \
                    ["content-md5", "etag", "last-modified", "content-length"]:
                    data.append((header[0], header[1]))
            if len(data) > 0:
                data = urllib.urlencode(data)
                self.database.feeds[self.url] = data

def main(feeds, maildir_root, database, options, config):
    if config.has_option('general', 'maildir_template'):
        maildir_template = config.get('general', 'maildir_template')
    else:
        maildir_template = '{}'

    for url in feeds:
        if config.has_option(url, 'name'):
            name = config.get(url, 'name')
        else:
            name = urllib.urlencode((('', url), )).split("=")[1]

        if config.has_option(url, 'maildir'):
            relative_maildir = config.get(url, 'maildir')
        else:
            relative_maildir = maildir_template.replace('{}', name)

        maildir = os.path.join(maildir_root, relative_maildir)

        try:
            make_maildir(maildir)
        except OSError as e:
            log.warning('Could not create maildir %s: %s' % (maildir, str(e)))
            log.warning('Skipping feed %s' % url)
            continue

        # right - we've got the directories, we've got the url, we know the
        # url... lets play!

        feed = Feed(database, url)
        feed.parse_and_deliver(maildir)
