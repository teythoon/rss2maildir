#!/usr/bin/python

import unittest
import sys
import os

class UnorderedListTests(unittest.TestCase):
    def setUp(self):
        self.inputpath = os.path.sep.join(os.path.dirname(os.path.realpath(__file__)).split(os.path.sep)[0:-1])

    def testwellformedlist(self):
        try:
            from rss2maildir import HTML2Text
        except:
            sys.path.append(os.path.sep.join(self.inputpath.split(os.path.sep)[0:-1]))
            try:
                from rss2maildir import HTML2Text
            except:
                self.assert_(False)
        input_path = os.path.sep.join(os.path.dirname(os.path.realpath(__file__)).split(os.path.sep)[0:-1])
        input = open(os.path.join(input_path, "html", "unorderedlist-wellformed.html")).read()
        expectedoutput = open(os.path.join(input_path, "expected", "unorderedlist-wellformed.txt")).read()
        parser = HTML2Text()
        parser.feed(input)
        output = parser.gettext()
        self.assertEqual(output, expectedoutput)

    def testbadlyformed(self):
        try:
            from rss2maildir import HTML2Text
        except:
            sys.path.append(os.path.sep.join(self.inputpath.split(os.path.sep)[0:-1]))
            try:
                from rss2maildir import HTML2Text
            except:
                self.assert_(False)

        input_path = os.path.sep.join(os.path.dirname(os.path.realpath(__file__)).split(os.path.sep)[0:-1])
        input = open(os.path.join(input_path, "html", "unorderedlist-badlyformed.html")).read()
        expectedoutput = open(os.path.join(input_path, "expected", "unorderedlist-badlyformed.txt")).read()
        parser = HTML2Text()
        parser.feed(input)
        output = parser.gettext()
        self.assertEqual(output, expectedoutput)

if __name__ == "__main__":
    unittest.main()
