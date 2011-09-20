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

import textwrap
from HTMLParser import HTMLParser

class HTML2Text(HTMLParser):
    entities = {
        u'amp': u'&',
        u'lt': u'<',
        u'gt': u'>',
        u'pound': u'£',
        u'copy': u'©',
        u'apos': u'\'',
        u'quot': u'"',
        u'nbsp': u' ',
        u'ldquo': u'“',
        u'rdquo': u'”',
        u'lsquo': u'‘',
        u'rsquo': u'’',
        u'laquo': u'«',
        u'raquo': u'»',
        u'lsaquo': u'‹',
        u'rsaquo': u'›',
        u'bull': u'•',
        u'middot': u'·',
        u'deg': u'°',
        u'helip': u'…',
        u'trade': u'™',
        u'reg': u'®',
        u'agrave': u'à',
        u'Agrave': u'À',
        u'egrave': u'è',
        u'Egrave': u'È',
        u'igrave': u'ì',
        u'Igrave': u'Ì',
        u'ograve': u'ò',
        u'Ograve': u'Ò',
        u'ugrave': u'ù',
        u'Ugrave': u'Ù',
        u'aacute': u'á',
        u'Aacute': u'Á',
        u'eacute': u'é',
        u'Eacute': u'É',
        u'iacute': u'í',
        u'Iacute': u'Í',
        u'oacute': u'ó',
        u'Oacute': u'Ó',
        u'uacute': u'ú',
        u'Uacute': u'Ú',
        u'yactue': u'ý',
        u'Yacute': u'Ý',
        u'acirc': u'â',
        u'Acirc': u'Â',
        u'ecirc': u'ê',
        u'Ecirc': u'Ê',
        u'icirc': u'î',
        u'Icirc': u'Î',
        u'ocirc': u'ô',
        u'Ocirc': u'Ô',
        u'ucirc': u'û',
        u'Ucirc': u'Û',
        u'atilde': u'ã',
        u'Atilde': u'Ã',
        u'ntilde': u'ñ',
        u'Ntilde': u'Ñ',
        u'otilde': u'õ',
        u'Otilde': u'Õ',
        u'auml': u'ä',
        u'Auml': u'Ä',
        u'euml': u'ë',
        u'Euml': u'Ë',
        u'iuml': u'ï',
        u'Iuml': u'Ï',
        u'ouml': u'ö',
        u'Ouml': u'Ö',
        u'uuml': u'ü',
        u'Uuml': u'Ü',
        u'yuml': u'ÿ',
        u'Yuml': u'Ÿ',
        u'iexcl': u'¡',
        u'iquest': u'¿',
        u'ccedil': u'ç',
        u'Ccedil': u'Ç',
        u'oelig': u'œ',
        u'OElig': u'Œ',
        u'szlig': u'ß',
        u'oslash': u'ø',
        u'Oslash': u'Ø',
        u'aring': u'å',
        u'Aring': u'Å',
        u'aelig': u'æ',
        u'AElig': u'Æ',
        u'thorn': u'þ',
        u'THORN': u'Þ',
        u'eth': u'ð',
        u'ETH': u'Ð',
        u'mdash': u'—',
        u'ndash': u'–',
        u'sect': u'§',
        u'para': u'¶',
        u'uarr': u'↑',
        u'darr': u'↓',
        u'larr': u'←',
        u'rarr': u'→',
        u'dagger': u'†',
        u'Dagger': u'‡',
        u'permil': u'‰',
        u'prod': u'∏',
        u'infin': u'∞',
        u'radic': u'√',
        u'there4': u'∴',
        u'int': u'∫',
        u'asymp': u'≈',
        u'ne': u'≠',
        u'equiv': '≡',
        u'le': u'≤',
        u'ge': u'≥',
        u'loz': u'⋄',
        u'sum': u'∑',
        u'part': u'∂',
        u'prime': u'′',
        u'Prime': u'″',
        u'harr': u'↔',
        u'micro': u'µ',
        u'not': u'¬',
        u'plusmn': u'±',
        u'divide': u'÷',
        u'cent': u'¢',
        u'euro': u'€',
        }

    blockleveltags = [
        u'h1',
        u'h2',
        u'h3',
        u'h4',
        u'h5',
        u'h6',
        u'pre',
        u'p',
        u'ul',
        u'ol',
        u'dl',
        u'li',
        u'dt',
        u'dd',
        u'div',
        u'blockquote',
        ]

    liststarttags = [
        u'ul',
        u'ol',
        u'dl',
        ]

    cancontainflow = [
        u'div',
        u'li',
        u'dd',
        u'blockquote',
    ]

    def __init__(self, textwidth = 70):
        self.text = u''
        self.curdata = u''
        self.textwidth = textwidth
        self.opentags = []
        self.indentlevel = 0
        self.ignorenodata = False
        self.listcount = []
        self.urls = []
        self.images = {}
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        tag_name = tag.lower()
        if tag_name in self.blockleveltags:
            # handle starting a new block - unless we're in a block element
            # that can contain other blocks, we'll assume that we want to close
            # the container
            if len(self.opentags) > 1 and self.opentags[-1] == u'li':
                self.handle_curdata()

            if tag_name == u'ol':
                self.handle_curdata()
                self.listcount.append(1)
                self.listlevel = len(self.listcount) - 1

            if tag_name == u'dl':
                self.indentlevel = self.indentlevel + 4

            if tag_name in self.liststarttags:
                smallist = self.opentags[-3:-1]
                smallist.reverse()
                for prev_listtag in smallist:
                    if prev_listtag in [u'dl', u'ol']:
                        self.indentlevel = self.indentlevel + 4
                        break
                    elif prev_listtag == u'ul':
                        self.indentlevel = self.indentlevel + 3
                        break

            if len(self.opentags) > 0:
                self.handle_curdata()
                if tag_name not in self.cancontainflow:
                    self.opentags.pop()
            self.opentags.append(tag_name)
        else:
            if tag_name == "span":
                return
            listcount = 0
            try:
                listcount = self.listcount[-1]
            except:
                pass

            if tag_name == u'dd' and len(self.opentags) > 1 \
                and self.opentags[-1] == u'dt':
                self.handle_curdata()
                self.opentags.pop()
            elif tag_name == u'dt' and len(self.opentags) > 1 \
                and self.opentags[-1] == u'dd':
                self.handle_curdata()
                self.opentags.pop()
            elif tag_name == u'a':
                for attr in attrs:
                    if attr[0].lower() == u'href':
                        self.urls.append(attr[1].decode('utf-8'))
                self.curdata = self.curdata + u'`'
                self.opentags.append(tag_name)
                return
            elif tag_name == u'img':
                self.handle_image(attrs)
                return
            elif tag_name == u'br':
                self.handle_br()
                return
            else:
                # we don't know the tag, so lets avoid handling it!
                return 

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == u'br':
            self.handle_br()
        elif tag.lower() == u'img':
            self.handle_image(attrs)
            return

    def handle_br(self):
            self.handle_curdata()
            self.opentags.append(u'br')
            self.handle_curdata()
            self.opentags.pop()

    def handle_image(self, attrs):
        alt = u''
        url = u''
        for attr in attrs:
            if attr[0] == 'alt':
                alt = attr[1].decode('utf-8')
            elif attr[0] == 'src':
                url = attr[1].decode('utf-8')
        if url:
            if alt:
                if self.images.has_key(alt):
                    if self.images[alt]["url"] == url:
                        self.curdata = self.curdata \
                            + u'|%s|' %(alt,)
                    else:
                        while self.images.has_key(alt):
                            alt = alt + "_"
                        self.images[alt] = {"url": url}
                        self.curdata = self.curdata \
                            + u'|%s|' %(alt,)
                else:
                    self.images[alt] = {"url": url}
                    self.curdata = self.curdata \
                        + u'|%s|' %(alt,)
            else:
                if self.images.has_key(url):
                    self.curdata = self.curdata \
                        + u'|%s|' %(url,)
                else:
                    self.images[url] = {}
                    self.images[url]["url"] =url
                    self.curdata = self.curdata \
                        + u'|%s|' %(url,)

    def handle_curdata(self):
        if len(self.opentags) == 0:
            return

        tag_thats_done = self.opentags[-1]

        if len(self.curdata) == 0:
            return

        if tag_thats_done == u'br':
            if len(self.text) == 0 or self.text[-1] != '\n':
                self.text = self.text + '\n'
                self.ignorenodata = True
            return

        if len(self.curdata.strip()) == 0:
            return

        if tag_thats_done in self.blockleveltags:
            newlinerequired = self.text != u''
            if self.ignorenodata:
                newlinerequired = False
            self.ignorenodata = False
            if newlinerequired:
                if tag_thats_done in [u'dt', u'dd', u'li'] \
                    and len(self.text) > 1 \
                    and self.text[-1] != u'\n':
                        self.text = self.text + u'\n'
                elif len(self.text) > 2 \
                    and self.text[-1] != u'\n' \
                    and self.text[-2] != u'\n':
                    self.text = self.text + u'\n\n'

        if tag_thats_done in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            underline = u''
            underlinechar = u'='
            headingtext = " ".join(self.curdata.split())
            seperator = u'\n' + u' '*self.indentlevel
            headingtext = seperator.join( \
                textwrap.wrap( \
                    headingtext, \
                    self.textwidth - self.indentlevel \
                    ) \
                )

            if tag_thats_done == u'h2':
                underlinechar = u'-'
            elif tag_thats_done != u'h1':
                underlinechar = u'~'

            if u'\n' in headingtext:
                underline = u' ' * self.indentlevel \
                    + underlinechar * (self.textwidth - self.indentlevel)
            else:
                underline = u' ' * self.indentlevel \
                    + underlinechar * len(headingtext)
            self.text = self.text \
                + headingtext + u'\n' \
                + underline
        elif tag_thats_done in [u'p', u'div']:
            paragraph = unicode( \
                " ".join(self.curdata.strip().encode("utf-8").split()), \
                "utf-8")
            seperator = u'\n' + u' ' * self.indentlevel
            self.text = self.text \
                + u' ' * self.indentlevel \
                + seperator.join( \
                    textwrap.wrap( \
                        paragraph, self.textwidth - self.indentlevel))
        elif tag_thats_done == "pre":
            self.text = self.text + unicode( \
                self.curdata.encode("utf-8"), "utf-8")
        elif tag_thats_done == u'blockquote':
            quote = unicode( \
                " ".join(self.curdata.encode("utf-8").strip().split()), \
                "utf-8")
            seperator = u'\n' + u' ' * self.indentlevel + u'    '
            if len(self.text) > 0 and self.text[-1] != u'\n':
                self.text = self.text + u'\n'
            self.text = self.text \
                + u'    ' \
                + seperator.join( \
                    textwrap.wrap( \
                        quote, \
                        self.textwidth - self.indentlevel - 2 \
                    )
                )
            self.curdata = u''
        elif tag_thats_done == "li":
            item = unicode(self.curdata.encode("utf-8").strip(), "utf-8")
            if len(self.text) > 0 and self.text[-1] != u'\n':
                self.text = self.text + u'\n'
            # work out if we're in an ol rather than a ul
            latesttags = self.opentags[-4:]
            latesttags.reverse()
            isul = None
            for thing in latesttags:
                if thing == 'ul':
                    isul = True
                    break
                elif thing == 'ol':
                    isul = False
                    break

            listindent = 3
            if not isul:
                listindent = 4

            listmarker = u' * '
            if isul == False:
                listmarker = u' %2d. ' %(self.listcount[-1])
                self.listcount[-1] = self.listcount[-1] + 1

            seperator = u'\n' \
                + u' ' * self.indentlevel \
                + u' ' * listindent
            self.text = self.text \
                + u' ' * self.indentlevel \
                + listmarker \
                + seperator.join( \
                    textwrap.wrap( \
                        item, \
                        self.textwidth - self.indentlevel - listindent \
                    ) \
                )
            self.curdata = u''
        elif tag_thats_done == u'dt':
            definition = unicode(" ".join( \
                    self.curdata.encode("utf-8").strip().split()), \
                "utf-8")
            if len(self.text) > 0 and self.text[-1] != u'\n':
                self.text = self.text + u'\n\n'
            elif len(self.text) > 1 and self.text[-2] != u'\n':
                self.text = self.text + u'\n'
            definition = u' ' * (self.indentlevel - 4) + definition + "::"
            indentstring = u'\n' + u' ' * (self.indentlevel - 3)
            self.text = self.text \
                + indentstring.join(
                    textwrap.wrap(definition, \
                        self.textwidth - self.indentlevel - 4))
            self.curdata = u''
        elif tag_thats_done == u'dd':
            definition = unicode(" ".join( \
                    self.curdata.encode("utf-8").strip().split()),
                "utf-8")
            if len(definition) > 0:
                if len(self.text) > 0 and self.text[-1] != u'\n':
                    self.text = self.text + u'\n'
                indentstring = u'\n' + u' ' * self.indentlevel
                self.text = self.text \
                    + indentstring \
                    + indentstring.join( \
                        textwrap.wrap( \
                            definition, \
                            self.textwidth - self.indentlevel \
                            ) \
                        )
                self.curdata = u''
        elif tag_thats_done == u'a':
            self.curdata = self.curdata + u'`__'
            pass
        elif tag_thats_done in self.liststarttags:
            pass

        if tag_thats_done in self.blockleveltags:
            self.curdata = u''

        self.ignorenodata = False

    def handle_endtag(self, tag):
        self.ignorenodata = False
        if tag == "span":
            return

        try:
            tagindex = self.opentags.index(tag)
        except:
            return
        tag = tag.lower()

        if tag in [u'br', u'img']:
            return

        if tag == u'dl':
            self.indentlevel = self.indentlevel - 4

        if tag in self.liststarttags:
            if tag in [u'ol', u'dl', u'ul', u'dd']:
                self.handle_curdata()
                # find if there was a previous list level
                smalllist = self.opentags[:-1]
                smalllist.reverse()
                for prev_listtag in smalllist:
                    if prev_listtag in [u'ol', u'dl']:
                        self.indentlevel = self.indentlevel - 4
                        break
                    elif prev_listtag == u'ul':
                        self.indentlevel = self.indentlevel - 3
                        break

        if tag == u'ol':
            self.listcount = self.listcount[:-1]

        while tagindex < len(self.opentags) \
            and tag in self.opentags[tagindex+1:]:
            try:
                tagindex = self.opentags.index(tag, tagindex+1)
            except:
                # well, we don't want to do that then
                pass
        if tagindex != len(self.opentags) - 1:
            # Assuming the data was for the last opened tag first
            self.handle_curdata()
            # Now kill the list to be a slice before this tag was opened
            self.opentags = self.opentags[:tagindex + 1]
        else:
            self.handle_curdata()
            if self.opentags[-1] == tag:
                self.opentags.pop()

    def handle_data(self, data):
        if len(self.opentags) == 0:
            self.opentags.append(u'p')
        self.curdata = self.curdata + data.decode("utf-8")

    def handle_charref(self, name):
        try:
            entity = unichr(int(name))
        except:
            if name[0] == 'x':
                try:
                    entity = unichr(int('0%s' %(name,), 16))
                except:
                    entity = u'#%s' %(name,)
            else:
                entity = u'#%s' %(name,)
        self.curdata = self.curdata + unicode(entity.encode('utf-8'), \
            "utf-8")

    def handle_entityref(self, name):
        entity = name
        if HTML2Text.entities.has_key(name):
            entity = HTML2Text.entities[name]
        else:
            entity = "&" + name + ";"

        self.curdata = self.curdata + unicode(entity.encode('utf-8'), \
            "utf-8")

    def gettext(self):
        self.handle_curdata()
        if len(self.text) == 0 or self.text[-1] != u'\n':
            self.text = self.text + u'\n'
        self.opentags = []
        if len(self.text) > 0:
            while len(self.text) > 1 and self.text[-1] == u'\n':
                self.text = self.text[:-1]
            self.text = self.text + u'\n'
        if len(self.urls) > 0:
            self.text = self.text + u'\n__ ' + u'\n__ '.join(self.urls) + u'\n'
            self.urls = []
        if len(self.images.keys()) > 0:
            self.text = self.text + u'\n.. ' \
                + u'\n.. '.join( \
                    ["|%s| image:: %s" %(a, self.images[a]["url"]) \
                for a in self.images.keys()]) + u'\n'
            self.images = {}
        return self.text
