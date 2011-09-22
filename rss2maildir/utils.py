# coding=utf-8

# rss2maildir.py - RSS feeds to Maildir 1 email per item
#
# Copyright (C) 2007  Brett Parker <iDunno@sommitrealweird.co.uk>
# Copyright (C) 2011  Justus Winter <4winter@informatik.uni-hamburg.de>
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
import errno
import socket
import urllib
import httplib
import logging

log = logging.getLogger('rss2maildir')

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def make_maildir(path):
    for dirname in (os.path.join(path, subdir)
                    for subdir in ('cur', 'tmp', 'new')):
        mkdir_p(dirname)

def open_url(method, url):
    redirectcount = 0
    while redirectcount < 3:
        (type_, rest) = urllib.splittype(url)
        (host, path) = urllib.splithost(rest)
        (host, port) = urllib.splitport(host)
        if type_ == "https":
            if port == None:
                port = 443
        elif port == None:
            port = 80

        try:
            if type_ == "http":
                conn = httplib.HTTPConnection("%s:%s" %(host, port))
            else:
                conn = httplib.HTTPSConnection("%s:%s" %(host, port))
            conn.request(method, path)
        except (httplib.HTTPException, socket.error) as e:
            log.warning('http request %s %s failed: %s' % (method, url, str(e)))
            return None

        response = conn.getresponse()
        if response.status in [301, 302, 303, 307]:
            headers = response.getheaders()
            for header in headers:
                if header[0] == "location":
                    url = header[1]
        elif response.status == 200:
            return response
        redirectcount = redirectcount + 1
    return None
