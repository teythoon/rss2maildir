#!/usr/bin/python

import mailbox
import sys
import os
import stat
import urllib

from optparse import OptionParser
from ConfigParser import SafeConfigParser

# first off, parse the command line arguments

oparser = OptionParser()
oparser.add_option(
    "-c", "--conf", dest="conf",
    help="location of config file"
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
                    sys.stderr.write("Broken maildir: %s" %(maildir))
            try:
                mode = os.stat(os.path.join(maildir, "tmp"))[stat.ST_MODE]
            except:
                os.mkdir(os.path.join(maildir, "tmp"))
                if not stat.S_ISDIR(mode):
                    sys.stderr.write("Broken maildir: %s" %(maildir))
            try:
                mode = os.stat(os.path.join(maildir, "new"))[stat.ST_MODE]
                if not stat.S_ISDIR(mode):
                    sys.stderr.write("Broken maildir: %s" %(maildir))
            except:
                os.mkdir(os.path.join(maildir, "new"))
        else:
            sys.stderr.write("Broken maildir: %s" %(maildir))
    except:
        os.mkdir(maildir)
        os.mkdir(os.path.join(maildir, "new"))
        os.mkdir(os.path.join(maildir, "cur"))
        os.mkdir(os.path.join(maildir, "tmp"))
