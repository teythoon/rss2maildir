#!/usr/bin/python

import unittest
import sys
import os

class ParsingTest(unittest.TestCase):
    def setUp(self):
        self.inputpath = os.path.sep.join(os.path.dirname(os.path.realpath(__file__)).split(os.path.sep)[0:-1])

    def runParsingTest(self, filename):
        from rss2maildir.HTML2Text import HTML2Text
        input_path = os.path.sep.join(os.path.dirname(os.path.realpath(__file__)).split(os.path.sep)[0:-1])
        input = unicode(open(os.path.join(input_path, "html", filename + ".html")).read(), 'utf-8')
        expectedoutput = unicode(open(os.path.join(input_path, "expected", filename + ".txt")).read(), 'utf-8')
        parser = HTML2Text()
        parser.feed(input)
        output = parser.gettext()
        self.assertEqual(output, expectedoutput)
