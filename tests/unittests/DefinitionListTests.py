#!/usr/bin/python

import unittest
import sys
import os

class DefinitionListTests(unittest.TestCase):
    def setUp(self):
        self.inputpath = os.path.sep.join(os.path.dirname(os.path.realpath(__file__)).split(os.path.sep)[0:-1])

    def testWellFormedDefinitionList(self):
        try:
            from rss2maildir import HTML2Text
        except:
            sys.path.append(os.path.sep.join(self.inputpath.split(os.path.sep)[0:-1]))
            try:
                from rss2maildir import HTML2Text
            except:
                self.assert_(False)
        input_path = os.path.sep.join(os.path.dirname(os.path.realpath(__file__)).split(os.path.sep)[0:-1])
        input = open(os.path.join(input_path, "html", "definitionlist-wellformed.html")).read()
        expectedoutput = open(os.path.join(input_path, "expected", "definitionlist-wellformed.txt")).read()
        parser = HTML2Text()
        parser.feed(input)
        output = parser.gettext()
        self.assertEqual(output, expectedoutput)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(DefinitionListTests("testWellFormedDefinitionList"))
    return suite

if __name__ == "__main__":
    unittest.main()
