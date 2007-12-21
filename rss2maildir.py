#!/usr/bin/python
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
import httplib
import urllib

import feedparser

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

import datetime
import random
import string
import textwrap

import socket

from optparse import OptionParser
from ConfigParser import SafeConfigParser

from base64 import b64encode
import md5

import cgi
import dbm

from HTMLParser import HTMLParser

entities = {
    "amp": "&",
    "lt": "<",
    "gt": ">",
    "pound": "£",
    "copy": "©",
    "apos": "'",
    "quote": "\"",
    "nbsp": " ",
    }

class HTML2Text(HTMLParser):

    def __init__(self):
        self.inheadingone = False
        self.inheadingtwo = False
        self.inotherheading = False
        self.inparagraph = True
        self.inblockquote = False
        self.inlink = False
        self.text = u''
        self.currentparagraph = u''
        self.headingtext = u''
        self.blockquote = u''
        self.inpre = False
        self.inul = False
        self.initem = False
        self.item = u''
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "h1":
            self.inheadingone = True
            self.inparagraph = False
        elif tag.lower() == "h2":
            self.inheadingtwo = True
            self.inparagraph = False
        elif tag.lower() in ["h3", "h4", "h5", "h6"]:
            self.inotherheading = True
            self.inparagraph = False
        elif tag.lower() == "a":
            self.inlink = True
        elif tag.lower() == "br":
            self.handle_br()
        elif tag.lower() == "blockquote":
            self.inblockquote = True
            self.text = self.text + u'\n'
        elif tag.lower() == "p":
            if self.text != "":
                self.text = self.text + u'\n\n'
            if self.inparagraph:
                self.text = self.text \
                    + u'\n'.join(textwrap.wrap(self.currentparagraph, 70))
            self.currentparagraph = u''
            self.inparagraph = True
        elif tag.lower() == "pre":
            self.text = self.text + "\n"
            self.inpre = True
            self.inparagraph = False
            self.inblockquote = False
        elif tag.lower() == "ul":
            self.item = u''
            self.inul = True
            self.text = self.text + "\n"
        elif tag.lower() == "li" and self.inul:
            if not self.initem:
                self.initem = True
                self.item = u''
            else:
                self.text = self.text \
                    + u' * ' \
                    + u'\n   '.join([a.strip() for a in \
                        textwrap.wrap(self.item, 67)]) \
                    + u'\n'
                self.item = u''

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == "br":
            self.handle_br()

    def handle_br(self):
            if self.inparagraph:
                self.text = self.text \
                + u'\n'.join( \
                    [a \
                        for a in textwrap.wrap( \
                            self.currentparagraph, 70) \
                    ] \
                ) \
                + u'\n'
                self.currentparagraph = u''
            elif self.inblockquote:
                self.text = self.text \
                    + u'\n> ' \
                    + u'\n> '.join( \
                        [a \
                            for a in textwrap.wrap( \
                                self.blockquote.encode("utf-8") \
                                , 68) \
                        ] \
                    ) \
                    + u'\n'
                self.blockquote = u''
            else:
                self.text = self.text + "\n"

    def handle_endtag(self, tag):
        if tag.lower() == "h1":
            self.inheadingone = False
            self.text = self.text \
                + u'\n\n' \
                + self.headingtext.encode("utf-8") \
                + u'\n' \
                + u'=' * len(self.headingtext.encode("utf-8").strip())
            self.headingtext = u''
        elif tag.lower() == "h2":
            self.inheadingtwo = False
            self.text = self.text \
                + u'\n\n' \
                + self.headingtext.encode("utf-8") \
                + u'\n' \
                + u'-' * len(self.headingtext.encode("utf-8").strip())
            self.headingtext = u''
        elif tag.lower() in ["h3", "h4", "h5", "h6"]:
            self.inotherheading = False
            self.text = self.text \
                + u'\n\n' \
                + self.headingtext.encode("utf-8") \
                + u'\n' \
                + u'~' * len(self.headingtext.encode("utf-8").strip())
            self.headingtext = u''
        elif tag.lower() == "p":
            self.text = self.text \
                + u'\n'.join(textwrap.wrap( \
                    self.currentparagraph, 70) \
                )
            self.inparagraph = False
            self.currentparagraph = u''
        elif tag.lower() == "blockquote":
            self.text = self.text \
                + u'\n> ' \
                + u'\n> '.join( \
                    [a.strip() \
                        for a in textwrap.wrap( \
                            self.blockquote, 68)] \
                    ) \
                + u'\n'
            self.inblockquote = False
            self.blockquote = u''
        elif tag.lower() == "pre":
            self.inpre = False
        elif tag.lower() == "li":
            self.initem = False
            if self.item != "":
                self.text = self.text \
                    + u' * ' \
                    + u'\n   '.join( \
                        [a.strip() for a in textwrap.wrap(self.item, 67)]) \
                    + u'\n'
            self.item = u''
        elif tag.lower() == "ul":
            self.inul = False

    def handle_data(self, data):
        if self.inheadingone or self.inheadingtwo or self.inotherheading:
            self.headingtext = self.headingtext \
                + unicode(data, "utf-8").strip() \
                + u' '
        elif self.inblockquote:
            self.blockquote = self.blockquote \
                + unicode(data, "utf-8").strip() \
                + u' '
        elif self.inparagraph:
            self.currentparagraph = self.currentparagraph \
                + unicode(data, "utf-8").strip() \
                + u' '
        elif self.inul and self.initem:
            self.item = self.item + unicode(data, "utf-8")
        elif self.inpre:
            self.text = self.text + unicode(data, "utf-8")
        else:
            self.text = self.text + unicode(data, "utf-8").strip() + u' '

    def handle_entityref(self, name):
        entity = name
        if entities.has_key(name.lower()):
            entity = entities[name.lower()]
        elif name[0] == "#":
            entity = unichr(int(name[1:]))
        else:
            entity = "&" + name + ";"

        if self.inparagraph:
            self.currentparagraph = self.currentparagraph \
                + unicode(entity, "utf-8")
        elif self.inblockquote:
            self.blockquote = self.blockquote + unicode(entity, "utf-8")
        else:
            self.text = self.text + unicode(entity, "utf-8")

    def gettext(self):
        data = self.text
        if self.inparagraph:
            data = data + "\n".join(textwrap.wrap(self.currentparagraph, 70))
        return data

def parse_and_deliver(maildir, url, statedir):
    feedhandle = None
    headers = None
    # first check if we know about this feed already
    feeddb = dbm.open(os.path.join(statedir, "feeds"), "c")
    # we need all the parts of the url 
    (type, rest) = urllib.splittype(url)
    (host, path) = urllib.splithost(rest)
    (host, port) = urllib.splitport(host)
    if port == None:
        port = 80
    if feeddb.has_key(url):
        data = feeddb[url]
        data = cgi.parse_qs(data)
        # now do a head on the feed to see if it's been updated
        conn = httplib.HTTPConnection("%s:%s" %(host, port))
        conn.request("HEAD", path)
        response = conn.getresponse()
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
            conn = httplib.HTTPConnection("%s:%s" %(host, port))
            conn.request("GET", path)
            response = conn.getresponse()
            headers = response.getheaders()
            feedhandle = response
        else:
            return # don't need to do anything, nothings changed.
    else:
        conn = httplib.HTTPConnection("%s:%s" %(host, port))
        conn.request("GET", path)
        response = conn.getresponse()
        headers = response.getheaders()
        feedhandle = response

    fp = feedparser.parse(feedhandle)
    db = dbm.open(os.path.join(statedir, "seen"), "c")
    for item in fp["items"]:
        # have we seen it before?
        # need to work out what the content is first...

        if item.has_key("content"):
            content = item["content"][0]["value"]
        else:
            content = item["summary"]

        md5sum = md5.md5(content.encode("utf-8")).hexdigest()

        prevmessageid = None

        if db.has_key(url + "|" + item["link"]):
            data = db[url + "|" + item["link"]]
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
        createddate = datetime.datetime(*item["updated_parsed"][0:6]) \
            .strftime("%a, %e %b %Y %T -0000")
        msg.add_header("Date", createddate)
        msg.add_header("Subject", item["title"])
        msg.set_default_type("text/plain")

        htmlpart = MIMEText(content.encode("utf-8"), "html", "utf-8")
        textparser = HTML2Text()
        textparser.feed(content.encode("utf-8"))
        textcontent = textparser.gettext()
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
        data = urllib.urlencode((
            ("message-id", messageid), \
            ("created", createddate), \
            ("contentmd5", md5sum) \
            ))
        db[url + "|" + item["link"]] = data

    if headers:
        data = []
        for header in headers:
            if header[0] in ["content-md5", "etag", "last-modified", "content-length"]:
                data.append((header[0], header[1]))
        if len(data) > 0:
            data = urllib.urlencode(data)
            feeddb[url] = data

    db.close()
    feeddb.close()

# first off, parse the command line arguments

oparser = OptionParser()
oparser.add_option(
    "-c", "--conf", dest="conf",
    help="location of config file"
    )
oparser.add_option(
    "-s", "--statedir", dest="statedir",
    help="location of directory to store state in"
    )

(options, args) = oparser.parse_args()

# check for the configfile

configfile = None

if options.conf != None:
    # does the file exist?
    try:
        os.stat(options.conf)
        configfile = options.conf
    except:
        # should exit here as the specified file doesn't exist
        sys.stderr.write( \
            "Config file %s does not exist. Exiting.\n" %(options.conf,))
        sys.exit(2)
else:
    # check through the default locations
    try:
        os.stat("%s/.rss2maildir.conf" %(os.environ["HOME"],))
        configfile = "%s/.rss2maildir.conf" %(os.environ["HOME"],)
    except:
        try:
            os.stat("/etc/rss2maildir.conf")
            configfile = "/etc/rss2maildir.conf"
        except:
            sys.stderr.write("No config file found. Exiting.\n")
            sys.exit(2)

# Right - if we've got this far, we've got a config file, now for the hard
# bits...

scp = SafeConfigParser()
scp.read(configfile)

maildir_root = "RSSMaildir"
state_dir = "state"

if options.statedir != None:
    state_dir = options.statedir
    try:
        mode = os.stat(state_dir)[stat.ST_MODE]
        if not stat.S_ISDIR(mode):
            sys.stderr.write( \
                "State directory (%s) is not a directory\n" %(state_dir))
            sys.exit(1)
    except:
        # try to make the directory
        try:
            os.mkdir(state_dir)
        except:
            sys.stderr.write("Couldn't create statedir %s" %(state_dir))
            sys.exit(1)
elif scp.has_option("general", "state_dir"):
    new_state_dir = scp.get("general", "state_dir")
    try:
        mode = os.stat(state_dir)[stat.ST_MODE]
        if not stat.S_ISDIR(mode):
            sys.stderr.write( \
                "State directory (%s) is not a directory\n" %(state_dir))
            sys.exit(1)
    except:
        # try to create it
        try:
            os.mkdir(new_state_dir)
            state_dir = new_state_dir
        except:
            sys.stderr.write( \
                "Couldn't create state directory %s\n" %(new_state_dir))
            sys.exit(1)
else:
    try:
        mode = os.stat(state_dir)[stat.ST_MODE]
        if not stat.S_ISDIR(mode):
            sys.stderr.write( \
                "State directory %s is not a directory\n" %(state_dir))
            sys.exit(1)
    except:
        try:
            os.mkdir(state_dir)
        except:
            sys.stderr.write( \
                "State directory %s could not be created\n" %(state_dir))
            sys.exit(1)

if scp.has_option("general", "maildir_root"):
    maildir_root = scp.get("general", "maildir_root")

try:
    mode = os.stat(maildir_root)[stat.ST_MODE]
    if not stat.S_ISDIR(mode):
        sys.stderr.write( \
            "Maildir Root %s is not a directory\n" \
            %(maildir_root))
        sys.exit(1)
except:
    try:
        os.mkdir(maildir_root)
    except:
        sys.stderr.write("Couldn't create Maildir Root %s\n" %(maildir_root))
        sys.exit(1)

feeds = scp.sections()
try:
    feeds.remove("general")
except:
    pass

for section in feeds:
    # check if the directory exists
    maildir = None
    try:
        maildir = scp.get(section, "maildir")
    except:
        maildir = section

    maildir = urllib.urlencode(((section, maildir),)).split("=")[1]
    maildir = os.path.join(maildir_root, maildir)

    try:
        exists = os.stat(maildir)
        if stat.S_ISDIR(exists[stat.ST_MODE]):
            # check if there's a new, cur and tmp directory
            try:
                mode = os.stat(os.path.join(maildir, "cur"))[stat.ST_MODE]
            except:
                os.mkdir(os.path.join(maildir, "cur"))
                if not stat.S_ISDIR(mode):
                    sys.stderr.write("Broken maildir: %s\n" %(maildir))
            try:
                mode = os.stat(os.path.join(maildir, "tmp"))[stat.ST_MODE]
            except:
                os.mkdir(os.path.join(maildir, "tmp"))
                if not stat.S_ISDIR(mode):
                    sys.stderr.write("Broken maildir: %s\n" %(maildir))
            try:
                mode = os.stat(os.path.join(maildir, "new"))[stat.ST_MODE]
                if not stat.S_ISDIR(mode):
                    sys.stderr.write("Broken maildir: %s\n" %(maildir))
            except:
                os.mkdir(os.path.join(maildir, "new"))
        else:
            sys.stderr.write("Broken maildir: %s\n" %(maildir))
    except:
        try:
            os.mkdir(maildir)
        except:
            sys.stderr.write("Couldn't create root maildir %s\n" %(maildir))
            sys.exit(1)
        try:
            os.mkdir(os.path.join(maildir, "new"))
            os.mkdir(os.path.join(maildir, "cur"))
            os.mkdir(os.path.join(maildir, "tmp"))
        except:
            sys.stderr.write( \
                "Couldn't create required maildir directories for %s\n" \
                %(section,))
            sys.exit(1)

    # right - we've got the directories, we've got the section, we know the
    # url... lets play!

    parse_and_deliver(maildir, section, state_dir)
