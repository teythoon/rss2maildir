import sys
import os
import codecs
import unittest

from rss2maildir.HTML2Text import HTML2Text

basepath = os.path.join(os.path.dirname(__file__), os.path.pardir)

class ParsingTest(unittest.TestCase):
    def runParsingTest(self, filename):
        input_ = codecs.open(os.path.join(basepath, 'html', filename + '.html'),
                             encoding = 'utf-8').read()
        expectedoutput = codecs.open(os.path.join(basepath, 'expected', filename + '.txt'),
                                     encoding = 'utf-8').read()

        parser = HTML2Text()
        parser.feed(input_)
        self.assertEqual(parser.gettext(), expectedoutput)
