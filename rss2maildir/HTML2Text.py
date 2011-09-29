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
    '''
    HTML2Text parses html fragments to a reStructuredText like
    representation.
    '''

    entities = {
        'amp': u'&',
        'lt': u'<',
        'gt': u'>',
        'pound': u'£',
        'copy': u'©',
        'apos': u'\'',
        'quot': u'"',
        'nbsp': u' ',
        'ldquo': u'“',
        'rdquo': u'”',
        'lsquo': u'‘',
        'rsquo': u'’',
        'laquo': u'«',
        'raquo': u'»',
        'lsaquo': u'‹',
        'rsaquo': u'›',
        'bull': u'•',
        'middot': u'·',
        'deg': u'°',
        'helip': u'…',
        'trade': u'™',
        'reg': u'®',
        'agrave': u'à',
        'Agrave': u'À',
        'egrave': u'è',
        'Egrave': u'È',
        'igrave': u'ì',
        'Igrave': u'Ì',
        'ograve': u'ò',
        'Ograve': u'Ò',
        'ugrave': u'ù',
        'Ugrave': u'Ù',
        'aacute': u'á',
        'Aacute': u'Á',
        'eacute': u'é',
        'Eacute': u'É',
        'iacute': u'í',
        'Iacute': u'Í',
        'oacute': u'ó',
        'Oacute': u'Ó',
        'uacute': u'ú',
        'Uacute': u'Ú',
        'yactue': u'ý',
        'Yacute': u'Ý',
        'acirc': u'â',
        'Acirc': u'Â',
        'ecirc': u'ê',
        'Ecirc': u'Ê',
        'icirc': u'î',
        'Icirc': u'Î',
        'ocirc': u'ô',
        'Ocirc': u'Ô',
        'ucirc': u'û',
        'Ucirc': u'Û',
        'atilde': u'ã',
        'Atilde': u'Ã',
        'ntilde': u'ñ',
        'Ntilde': u'Ñ',
        'otilde': u'õ',
        'Otilde': u'Õ',
        'auml': u'ä',
        'Auml': u'Ä',
        'euml': u'ë',
        'Euml': u'Ë',
        'iuml': u'ï',
        'Iuml': u'Ï',
        'ouml': u'ö',
        'Ouml': u'Ö',
        'uuml': u'ü',
        'Uuml': u'Ü',
        'yuml': u'ÿ',
        'Yuml': u'Ÿ',
        'iexcl': u'¡',
        'iquest': u'¿',
        'ccedil': u'ç',
        'Ccedil': u'Ç',
        'oelig': u'œ',
        'OElig': u'Œ',
        'szlig': u'ß',
        'oslash': u'ø',
        'Oslash': u'Ø',
        'aring': u'å',
        'Aring': u'Å',
        'aelig': u'æ',
        'AElig': u'Æ',
        'thorn': u'þ',
        'THORN': u'Þ',
        'eth': u'ð',
        'ETH': u'Ð',
        'mdash': u'—',
        'ndash': u'–',
        'sect': u'§',
        'para': u'¶',
        'uarr': u'↑',
        'darr': u'↓',
        'larr': u'←',
        'rarr': u'→',
        'dagger': u'†',
        'Dagger': u'‡',
        'permil': u'‰',
        'prod': u'∏',
        'infin': u'∞',
        'radic': u'√',
        'there4': u'∴',
        'int': u'∫',
        'asymp': u'≈',
        'ne': u'≠',
        'equiv': '≡',
        'le': u'≤',
        'ge': u'≥',
        'loz': u'⋄',
        'sum': u'∑',
        'part': u'∂',
        'prime': u'′',
        'Prime': u'″',
        'harr': u'↔',
        'micro': u'µ',
        'not': u'¬',
        'plusmn': u'±',
        'divide': u'÷',
        'cent': u'¢',
        'euro': u'€',
        }

    blockleveltags = [
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
        'pre',
        'p',
        'ul',
        'ol',
        'dl',
        'li',
        'dt',
        'dd',
        'div',
        'blockquote',
        ]

    liststarttags = [
        'ul',
        'ol',
        'dl',
        ]

    cancontainflow = [
        'div',
        'li',
        'dd',
        'blockquote',
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
            # handle starting a new block - '\n'ess we're in a block element
            # that can contain other blocks, we'll assume that we want to close
            # the container
            if len(self.opentags) > 1 and self.opentags[-1] == 'li':
                self.handle_curdata()

            if tag_name == 'ol':
                self.handle_curdata()
                self.listcount.append(1)
                self.listlevel = len(self.listcount) - 1

            if tag_name == 'dl':
                self.indentlevel = self.indentlevel + 4

            if tag_name in self.liststarttags:
                smallist = self.opentags[-3:-1]
                smallist.reverse()
                for prev_listtag in smallist:
                    if prev_listtag in ['dl', 'ol']:
                        self.indentlevel = self.indentlevel + 4
                        break
                    elif prev_listtag == 'ul':
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

            if tag_name == 'dd' and len(self.opentags) > 1 \
                and self.opentags[-1] == 'dt':
                self.handle_curdata()
                self.opentags.pop()
            elif tag_name == 'dt' and len(self.opentags) > 1 \
                and self.opentags[-1] == 'dd':
                self.handle_curdata()
                self.opentags.pop()
            elif tag_name == 'a':
                for attr in attrs:
                    if attr[0].lower() == 'href':
                        self.urls.append(attr[1].decode('utf-8'))
                self.curdata = self.curdata + '`'
                self.opentags.append(tag_name)
                return
            elif tag_name == 'img':
                self.handle_image(attrs)
                return
            elif tag_name == 'br':
                self.handle_br()
                return
            else:
                # we don't know the tag, so lets avoid handling it!
                return

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == 'br':
            self.handle_br()
        elif tag.lower() == 'img':
            self.handle_image(attrs)
            return

    def handle_br(self):
            self.handle_curdata()
            self.opentags.append('br')
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
                            + '|%s|' %(alt,)
                    else:
                        while self.images.has_key(alt):
                            alt = alt + "_"
                        self.images[alt] = {"url": url}
                        self.curdata = self.curdata \
                            + '|%s|' %(alt,)
                else:
                    self.images[alt] = {"url": url}
                    self.curdata = self.curdata \
                        + '|%s|' %(alt,)
            else:
                if self.images.has_key(url):
                    self.curdata = self.curdata \
                        + '|%s|' %(url,)
                else:
                    self.images[url] = {}
                    self.images[url]["url"] =url
                    self.curdata = self.curdata \
                        + '|%s|' %(url,)

    def handle_curdata(self):
        if len(self.opentags) == 0:
            return

        tag_thats_done = self.opentags[-1]

        if len(self.curdata) == 0:
            return

        if tag_thats_done == 'br':
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
                if tag_thats_done in ['dt', 'dd', 'li'] \
                    and len(self.text) > 1 \
                    and self.text[-1] != '\n':
                        self.text = self.text + '\n'
                elif len(self.text) > 2 \
                    and self.text[-1] != '\n' \
                    and self.text[-2] != '\n':
                    self.text = self.text + '\n\n'

        if tag_thats_done in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            underline = u''
            underlinechar = '='
            headingtext = " ".join(self.curdata.split())
            seperator = '\n' + ' '*self.indentlevel
            headingtext = seperator.join( \
                textwrap.wrap( \
                    headingtext, \
                    self.textwidth - self.indentlevel \
                    ) \
                )

            if tag_thats_done == 'h2':
                underlinechar = '-'
            elif tag_thats_done != 'h1':
                underlinechar = '~'

            if '\n' in headingtext:
                underline = ' ' * self.indentlevel \
                    + underlinechar * (self.textwidth - self.indentlevel)
            else:
                underline = ' ' * self.indentlevel \
                    + underlinechar * len(headingtext)
            self.text = self.text \
                + headingtext + '\n' \
                + underline
        elif tag_thats_done in ['p', 'div']:
            paragraph = unicode( \
                " ".join(self.curdata.strip().encode("utf-8").split()), \
                "utf-8")
            seperator = '\n' + ' ' * self.indentlevel
            self.text = self.text \
                + ' ' * self.indentlevel \
                + seperator.join( \
                    textwrap.wrap( \
                        paragraph, self.textwidth - self.indentlevel))
        elif tag_thats_done == "pre":
            self.text = self.text + unicode( \
                self.curdata.encode("utf-8"), "utf-8")
        elif tag_thats_done == 'blockquote':
            quote = unicode( \
                " ".join(self.curdata.encode("utf-8").strip().split()), \
                "utf-8")
            seperator = '\n' + ' ' * self.indentlevel + '    '
            if len(self.text) > 0 and self.text[-1] != '\n':
                self.text = self.text + '\n'
            self.text = self.text \
                + '    ' \
                + seperator.join( \
                    textwrap.wrap( \
                        quote, \
                        self.textwidth - self.indentlevel - 2 \
                    )
                )
            self.curdata = u''
        elif tag_thats_done == "li":
            item = unicode(self.curdata.encode("utf-8").strip(), "utf-8")
            if len(self.text) > 0 and self.text[-1] != '\n':
                self.text = self.text + '\n'
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

            listmarker = ' * '
            if isul == False:
                listmarker = ' %2d. ' %(self.listcount[-1])
                self.listcount[-1] = self.listcount[-1] + 1

            seperator = '\n' \
                + ' ' * self.indentlevel \
                + ' ' * listindent
            self.text = self.text \
                + ' ' * self.indentlevel \
                + listmarker \
                + seperator.join( \
                    textwrap.wrap( \
                        item, \
                        self.textwidth - self.indentlevel - listindent \
                    ) \
                )
            self.curdata = u''
        elif tag_thats_done == 'dt':
            definition = unicode(" ".join( \
                    self.curdata.encode("utf-8").strip().split()), \
                "utf-8")
            if len(self.text) > 0 and self.text[-1] != '\n':
                self.text = self.text + '\n\n'
            elif len(self.text) > 1 and self.text[-2] != '\n':
                self.text = self.text + '\n'
            definition = ' ' * (self.indentlevel - 4) + definition + "::"
            indentstring = '\n' + ' ' * (self.indentlevel - 3)
            self.text = self.text \
                + indentstring.join(
                    textwrap.wrap(definition, \
                        self.textwidth - self.indentlevel - 4))
            self.curdata = u''
        elif tag_thats_done == 'dd':
            definition = unicode(" ".join( \
                    self.curdata.encode("utf-8").strip().split()),
                "utf-8")
            if len(definition) > 0:
                if len(self.text) > 0 and self.text[-1] != '\n':
                    self.text = self.text + '\n'
                indentstring = '\n' + ' ' * self.indentlevel
                self.text = self.text \
                    + indentstring \
                    + indentstring.join( \
                        textwrap.wrap( \
                            definition, \
                            self.textwidth - self.indentlevel \
                            ) \
                        )
                self.curdata = u''
        elif tag_thats_done == 'a':
            self.curdata = self.curdata + '`__'
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

        if tag in ['br', 'img']:
            return

        if tag == 'dl':
            self.indentlevel = self.indentlevel - 4

        if tag in self.liststarttags:
            if tag in ['ol', 'dl', 'ul', 'dd']:
                self.handle_curdata()
                # find if there was a previous list level
                smalllist = self.opentags[:-1]
                smalllist.reverse()
                for prev_listtag in smalllist:
                    if prev_listtag in ['ol', 'dl']:
                        self.indentlevel = self.indentlevel - 4
                        break
                    elif prev_listtag == 'ul':
                        self.indentlevel = self.indentlevel - 3
                        break

        if tag == 'ol':
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
            self.opentags.append('p')
        self.curdata = self.curdata + data.decode("utf-8")

    def handle_charref(self, name):
        try:
            entity = unichr(int(name))
        except:
            if name[0] == 'x':
                try:
                    entity = unichr(int('0%s' %(name,), 16))
                except:
                    entity = '#%s' %(name,)
            else:
                entity = '#%s' %(name,)
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
        if len(self.text) == 0 or self.text[-1] != '\n':
            self.text = self.text + '\n'
        self.opentags = []
        if len(self.text) > 0:
            while len(self.text) > 1 and self.text[-1] == '\n':
                self.text = self.text[:-1]
            self.text = self.text + '\n'
        if len(self.urls) > 0:
            self.text = self.text + '\n__ ' + '\n__ '.join(self.urls) + '\n'
            self.urls = []
        if len(self.images.keys()) > 0:
            self.text = self.text + '\n.. ' \
                + '\n.. '.join( \
                    ["|%s| image:: %s" %(a, self.images[a]["url"]) \
                for a in self.images.keys()]) + '\n'
            self.images = {}
        return self.text
