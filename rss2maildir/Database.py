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
import dbm
import logging
import marshal

from .utils import mkdir_p

log = logging.getLogger('database')

serialize = marshal.dumps
deserialize = marshal.loads

class Database(object):
    def __init__(self, path):
        try:
            mkdir_p(path)
        except OSError as e:
            raise RuntimeError("Couldn't create statedir %s: %s" % (settings['state_dir'], str(e)))

        self.feeds = dbm.open(os.path.join(path, "feeds"), "c")
        self.seen = dbm.open(os.path.join(path, "seen"), "c")

    def __del__(self):
        self.feeds.close()
        self.seen.close()

    def seen_before(self, item):
        if item.db_guid_key:
            if self.seen.has_key(item.db_guid_key):
                data = deserialize(self.seen[item.db_guid_key])
                if data['contentmd5'] == item.md5sum:
                    return True

        if self.seen.has_key(item.db_link_key):
            data = deserialize(self.seen[item.db_link_key])

            if data.has_key('message-id'):
                item.previous_message_id = data['message-id']

            if data['contentmd5'] == item.md5sum:
                return True

        return False

    def mark_seen(self, item):
        if item.previous_message_id:
            item.message_id = item.previous_message_id + " " + item.message_id

        data = serialize({
            'message-id': item.message_id,
            'created': item.createddate,
            'contentmd5': item.md5sum
        })

        if item.guid and item.guid != item.link:
            self.seen[item.db_guid_key] = data
            try:
                previous_data = deserialize(self.seen[item.db_link_key])
                newdata = serialize({
                    'message-id': item.message_id,
                    'created': previous_data['created'],
                    'contentmd5': previous_data['contentmd5']
                })
                self.seen[item.db_link_key] = newdata
            except:
                self.seen[item.db_link_key] = data
        else:
            self.seen[item.db_link_key] = data

    def get_feed_metadata(self, url):
        return deserialize(self.feeds[url])

    def set_feed_metadata(self, url, data):
        self.feeds[url] = serialize(data)
