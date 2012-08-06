===========
rss2maildir
===========

Introduction
============

rss2maildir takes rss feeds and creates a maildir of messages for each of the
feeds, new items become "new", updated entries get redelivered as new messages.
Each feed becomes it's own maildir which can be named as you like.

Installation
============

Clone this repository or download the ZIP archive. Then run::

  ./setup.py install

to install the Python package and the command-line tool.

Usage
=====

Configuration
-------------

Create a config file containing the feeds and their "names" - the names will be
used as the directory name of the maildir for the feed. A complete example can
be found at `rss2maildir.conf.example`::

  [general]
  state_dir = "/path/to/a/writtable/directory/to/write/state/to"
  maildir_root = "/path/to/directory/to/write/maildirs/in"

  [http://path/to/a/rss/feed/]
  maildir = "name of folder to put mail in"


*  The state_dir in the general section defaults to the current working directory + `state`.

*  The maildir_root defaults to the current working directory + `RSSMaildir`.

*  It doesn't really matter where you save the config file.

Execution
---------

During installation, `setup.py` should have installed the command-line utility
`rss2maildir` into your path. Executing::

  rss2maildir -c ./path/to/your.config

will look for new feed items and place them into the maildirs. In order to
recieve new items into your maildirs, you need to execute it regularly.
