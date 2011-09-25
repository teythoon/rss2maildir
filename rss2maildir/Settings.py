# coding=utf-8

# rss2maildir.py - RSS feeds to Maildir 1 email per item
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
import ConfigParser

class FeedConfigParser(ConfigParser.SafeConfigParser):
    def __init__(self,
                 common_section_name = 'common',
                 general_section_name = 'general',
                 *args, **kwargs):
        ConfigParser.SafeConfigParser.__init__(self, *args, **kwargs)
        self.common_section_name = common_section_name
        self.general_section_name = general_section_name

    def get(self, section, key, *args, **kwargs):
        for location in (section, self.common_section_name):
            if self.has_option(location, key):
                return ConfigParser.SafeConfigParser.get(self, location, key, *args, **kwargs)

        raise KeyError('Neither section %s nor %s contained the option %s' %
                       (section, self.common_section_name, key))

    def __contains__(self, key):
        return self.has_option(self.general_section_name, key)

    def __getitem__(self, key):
        return ConfigParser.SafeConfigParser.get(self, self.general_section_name, key)

    def __setitem__(self, key, value):
        self.set(self.general_section_name, key, value)

    def feeds(self):
        return (section for section in self.sections()
                if section not in (self.general_section_name, self.common_section_name))

settings = FeedConfigParser()
settings.readfp(open(os.path.join(os.path.dirname(__file__), 'defaults', 'rss2maildir.conf')))
