#!/usr/bin/python

import mailbox
import sys
import os
import stat
import urllib

import feedparser

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

import datetime
import random
import string

import socket

from optparse import OptionParser
from ConfigParser import SafeConfigParser

from base64 import b64encode
import md5

import cgi
import dbm


def parse_and_deliver(maildir, url, statedir):
    md = mailbox.Maildir(maildir)
    fp = feedparser.parse(url)
    db = dbm.open(os.path.join(statedir, "seen"), "c")
    for item in fp["items"]:
        # have we seen it before?
        # need to work out what the content is first...

        if item.has_key("content"):
            content = item["content"][0]["value"]
        else:
            content = item["summary"]

        md5sum = md5.md5(content.encode("utf8")).hexdigest()

        if db.has_key(item["link"]):
            data = db[item["link"]]
            data = cgi.parse_qs(data)
            if data["contentmd5"][0] == md5sum:
                continue

        try:
            author = item["author"]
        except:
            author = url

        # create a basic email message
        msg = MIMEMultipart("alternative")
        messageid = "<" + datetime.datetime.now().strftime("%Y%m%d%H%M") + "." + "".join([random.choice(string.ascii_letters + string.digits) for a in range(0,6)]) + "@" + socket.gethostname() + ">"
        msg.add_header("Message-ID", messageid)
        msg.set_unixfrom("\"%s\" <rss2maildir@localhost>" %(url))
        msg.add_header("From", "\"%s\" <rss2maildir@localhost>" %(author))
        msg.add_header("To", "\"%s\" <rss2maildir@localhost>" %(url))
        createddate = datetime.datetime(*item["updated_parsed"][0:6]).strftime("%a, %e %b %Y %T -0000")
        msg.add_header("Date", createddate)
        msg.add_header("Subject", item["title"])
        msg.set_default_type("text/plain")

        htmlpart = MIMEText(content.encode("utf8"), "html", "utf8")
        textpart = MIMEText(content.encode("utf8"), "plain", "utf8")

        msg.attach(textpart)
        msg.attach(htmlpart)

        # start by working out the filename we should be writting to, we do
        # this following the normal maildir style rules
        fname = str(os.getpid()) + "." + socket.gethostname() + "." + "".join([random.choice(string.ascii_letters + string.digits) for a in range(0,10)]) + "." + datetime.datetime.now().strftime('%s')
        fn = os.path.join(maildir, "tmp", fname)
        fh = open(fn, "w")
        fh.write(msg.as_string())
        fh.close()
        # now move it in to the new directory
        newfn = os.path.join(maildir, "new", fname)
        os.link(fn, newfn)
        os.unlink(fn)

        # now add to the database about the item
        data = urllib.urlencode((("message-id", messageid), ("created", createddate), ("contentmd5", md5sum)))
        db[item["link"]] = data

    db.close()

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
        sys.stderr.write("Config file %s does not exist. Exiting.\n" %(options.conf,))
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
            sys.stderr.write("State directory (%s) is not a directory\n" %(state_dir))
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
            sys.stderr.write("State directory (%s) is not a directory\n" %(state_dir))
            sys.exit(1)
    except:
        # try to create it
        try:
            os.mkdir(new_state_dir)
            state_dir = new_state_dir
        except:
            sys.stderr.write("Couldn't create state directory %s\n" %(new_state_dir))
            sys.exit(1)
else:
    try:
        mode = os.stat(state_dir)[stat.ST_MODE]
        if not stat.S_ISDIR(mode):
            sys.stderr.write("State directory %s is not a directory\n" %(state_dir))
            sys.exit(1)
    except:
        try:
            os.mkdir(state_dir)
        except:
            sys.stderr.write("State directory %s could not be created\n" %(state_dir))
            sys.exit(1)

if scp.has_option("general", "maildir_root"):
    maildir_root = scp.get("general", "maildir_root")

try:
    mode = os.stat(maildir_root)[stat.ST_MODE]
    if not stat.S_ISDIR(mode):
        sys.stderr.write("Maildir Root %s is not a directory\n" %(maildir_root))
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
            sys.stderr.write("Couldn't create required maildir directories for %s\n" %(section,))
            sys.exit(1)

    # right - we've got the directories, we've got the section, we know the
    # url... lets play!

    parse_and_deliver(maildir, section, state_dir)
