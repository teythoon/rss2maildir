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
import email
import socket
import datetime

from .HTML2Text import HTML2Text
from .utils import generate_random_string, compute_hash

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

        self.md5sum = compute_hash(self.content.encode('utf-8'))

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

        self.previous_message_id = None
        self.message_id = '<%s.%s@%s>' % (
            datetime.datetime.now().strftime("%Y%m%d%H%M"),
            generate_random_string(6),
            socket.gethostname()
        )

    def __getitem__(self, key):
        return getattr(self, key)

    text_template = u'%(text_content)s\n\nItem URL: %(link)s'
    html_template = u'%(html_content)s\n<p>Item URL: <a href="%(link)s">%(link)s</a></p>'
    def create_message(self, include_html_part = True):
        message = email.MIMEMultipart.MIMEMultipart('alternative')

        message.set_unixfrom('%s <rss2maildir@localhost>' % self.feed.url)
        message.add_header('From', '%s <rss2maildir@localhost>' % self.author)
        message.add_header('To', '%s <rss2maildir@localhost>' % self.feed.url)

        subj_gen = HTML2Text()
        title = self.title.replace(u'<', u'&lt;').replace(u'>', u'&gt;')
        subj_gen.feed(title.encode('utf-8'))
        message.add_header('Subject', subj_gen.gettext())

        message.add_header('Message-ID', self.message_id)
        if self.previous_message_id:
            message.add_header('References', self.previous_message_id)

        message.add_header('Date', self.createddate)
        message.add_header('X-rss2maildir-rundate',
                       datetime.datetime.now().strftime('%a, %e %b %Y %T -0000'))

        textpart = email.MIMEText.MIMEText((self.text_template % self).encode('utf-8'),
                                           'plain', 'utf-8')
        message.set_default_type('text/plain')
        message.attach(textpart)

        if include_html_part:
            htmlpart = email.MIMEText.MIMEText((self.html_template % self).encode('utf-8'),
                                               'html', 'utf-8')
            message.attach(htmlpart)

        return message

    @property
    def text_content(self):
        textparser = HTML2Text()
        textparser.feed(self.content.encode('utf-8'))
        return textparser.gettext()

    @property
    def html_content(self):
        return self.content

    def deliver(self, message, maildir):
        # start by working out the filename we should be writting to, we do
        # this following the normal maildir style rules
        file_name = '%i.%s.%s.%s' % (
            os.getpid(),
            socket.gethostname(),
            generate_random_string(10),
            datetime.datetime.now().strftime('%s')
        )

        tmp_path = os.path.join(maildir, 'tmp', file_name)
        handle = open(tmp_path, 'w')
        handle.write(message.as_string())
        handle.close()

        # now move it in to the new directory
        new_path = os.path.join(maildir, 'new', file_name)
        os.link(tmp_path, new_path)
        os.unlink(tmp_path)
