#!/usr/bin/python

import mailbox
import sys
import os

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

feeds = scp.sections()
try:
    feeds.remove("general")
except:
    pass

for section in feeds:
    print section
    print "-" * len(section)
    print scp.items(section)
