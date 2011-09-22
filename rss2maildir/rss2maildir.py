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
import dbm

import re

from .HTML2Text import HTML2Text
from .utils import make_maildir, open_url

log = logging.getLogger('rss2maildir')

class NewsItem(object):
    def parse_and_deliver(self, maildir, url, feed_db, seen_db):
        feedhandle = None
        headers = None
        # first check if we know about this feed already
        if feed_db.has_key(url):
            data = feed_db[url]
            data = cgi.parse_qs(data)
            response = open_url("HEAD", url)
            headers = None
            if response:
                headers = response.getheaders()
            ischanged = False
            try:
                for header in headers:
                    if header[0] == "content-length":
                        if header[1] != data["content-length"][0]:
                            ischanged = True
                    elif header[0] == "etag":
                        if header[1] != data["etag"][0]:
                            ischanged = True
                    elif header[0] == "last-modified":
                        if header[1] != data["last-modified"][0]:
                            ischanged = True
                    elif header[0] == "content-md5":
                        if header[1] != data["content-md5"][0]:
                            ischanged = True
            except:
                ischanged = True
            if ischanged:
                response = open_url("GET", url)
                if response != None:
                    headers = response.getheaders()
                    feedhandle = response
                else:
                    sys.stderr.write("Failed to fetch feed: %s\n" %(url))
                    return
            else:
                return # don't need to do anything, nothings changed.
        else:
            response = open_url("GET", url)
            if response != None:
                headers = response.getheaders()
                feedhandle = response
            else:
                sys.stderr.write("Failed to fetch feed: %s\n" %(url))
                return

        fp = feedparser.parse(feedhandle)
        for item in fp["items"]:
            # have we seen it before?
            # need to work out what the content is first...

            if item.has_key("content"):
                content = item["content"][0]["value"]
            else:
                if item.has_key("description"):
                    content = item["description"]
                else:
                    content = u''

            md5sum = md5.md5(content.encode("utf-8")).hexdigest()

            prevmessageid = None

            db_guid_key = None
            db_link_key = (url + u'|' + item["link"]).encode("utf-8")

            # check if there's a guid too - if that exists and we match the md5,
            # return
            if item.has_key("guid"):
                db_guid_key = (url + u'|' + item["guid"]).encode("utf-8")
                if seen_db.has_key(db_guid_key):
                    data = seen_db[db_guid_key]
                    data = cgi.parse_qs(data)
                    if data["contentmd5"][0] == md5sum:
                        continue

            if seen_db.has_key(db_link_key):
                data = seen_db[db_link_key]
                data = cgi.parse_qs(data)
                if data.has_key("message-id"):
                    prevmessageid = data["message-id"][0]
                if data["contentmd5"][0] == md5sum:
                    continue

            try:
                author = item["author"]
            except:
                author = url

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
            msg.set_unixfrom("\"%s\" <rss2maildir@localhost>" %(url))
            msg.add_header("From", "\"%s\" <rss2maildir@localhost>" %(author))
            msg.add_header("To", "\"%s\" <rss2maildir@localhost>" %(url))
            if prevmessageid:
                msg.add_header("References", prevmessageid)
            createddate = datetime.datetime.now() \
                .strftime("%a, %e %b %Y %T -0000")
            try:
                createddate = datetime.datetime(*item["updated_parsed"][0:6]) \
                    .strftime("%a, %e %b %Y %T -0000")
            except:
                pass
            msg.add_header("Date", createddate)
            msg.add_header("X-rss2maildir-rundate", datetime.datetime.now() \
                .strftime("%a, %e %b %Y %T -0000"))
            subj_gen = HTML2Text()
            title = item["title"]
            title = re.sub(u'<', u'&lt;', title)
            title = re.sub(u'>', u'&gt;', title)
            subj_gen.feed(title.encode("utf-8"))
            msg.add_header("Subject", subj_gen.gettext())
            msg.set_default_type("text/plain")

            htmlcontent = content.encode("utf-8")
            htmlcontent = "%s\n\n<p>Item URL: <a href='%s'>%s</a></p>" %( \
                content, \
                item["link"], \
                item["link"] )
            htmlpart = MIMEText(htmlcontent.encode("utf-8"), "html", "utf-8")
            textparser = HTML2Text()
            textparser.feed(content.encode("utf-8"))
            textcontent = textparser.gettext()
            textcontent = "%s\n\nItem URL: %s" %( \
                textcontent, \
                item["link"] )
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
            if prevmessageid:
                messageid = prevmessageid + " " + messageid
            if item.has_key("guid") and item["guid"] != item["link"]:
                data = urllib.urlencode(( \
                    ("message-id", messageid), \
                    ("created", createddate), \
                    ("contentmd5", md5sum) \
                    ))
                seen_db[db_guid_key] = data
                try:
                    data = seen_db[db_link_key]
                    data = cgi.parse_qs(data)
                    newdata = urllib.urlencode(( \
                        ("message-id", messageid), \
                        ("created", data["created"][0]), \
                        ("contentmd5", data["contentmd5"][0]) \
                        ))
                    seen_db[db_link_key] = newdata
                except:
                    seen_db[db_link_key] = data
            else:
                data = urllib.urlencode(( \
                    ("message-id", messageid), \
                    ("created", createddate), \
                    ("contentmd5", md5sum) \
                    ))
                seen_db[db_link_key] = data

        if headers:
            data = []
            for header in headers:
                if header[0] in \
                    ["content-md5", "etag", "last-modified", "content-length"]:
                    data.append((header[0], header[1]))
            if len(data) > 0:
                data = urllib.urlencode(data)
                feed_db[url] = data

def main(feeds, maildir_root, state_dir, options, config):
    feed_db = dbm.open(os.path.join(state_dir, "feeds"), "c")
    seen_db = dbm.open(os.path.join(state_dir, "seen"), "c")

    if config.has_option('general', 'maildir_template'):
        maildir_template = config.get('general', 'maildir_template')
    else:
        maildir_template = '{}'

    for section in feeds:
        if config.has_option(section, 'name'):
            name = config.get(section, 'name')
        else:
            name = urllib.urlencode((('', section), )).split("=")[1]

        if config.has_option(section, 'maildir'):
            relative_maildir = config.get(section, 'maildir')
        else:
            relative_maildir = maildir_template.replace('{}', name)

        maildir = os.path.join(maildir_root, relative_maildir)

        try:
            make_maildir(maildir)
        except OSError as e:
            log.warning('Could not create maildir %s: %s' % (maildir, str(e)))
            log.warning('Skipping feed %s' % section)
            continue

        # right - we've got the directories, we've got the section, we know the
        # url... lets play!

        NewsItem().parse_and_deliver(maildir, section, feed_db, seen_db)

    seen_db.close()
    feed_db.close()
