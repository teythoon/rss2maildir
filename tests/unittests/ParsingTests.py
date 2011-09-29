import sys
import os
import glob
import codecs
import unittest

from rss2maildir.HTML2Text import HTML2Text

basepath = os.path.join(os.path.dirname(__file__), os.path.pardir)
input_path = os.path.join(basepath, 'html')
expected_path = os.path.join(basepath, 'expected')

class ParsingTest(unittest.TestCase):
    def __init__(self, description, input_filename, expected_filename):
        self.input_filename = input_filename
        self.expected_filename = expected_filename
        self.description = description
        unittest.TestCase.__init__(self)

    def __str__(self):
        return self.description

    def runTest(self):
        input_ = codecs.open(self.input_filename, encoding = 'utf-8').read()
        expected_ = codecs.open(self.expected_filename, encoding = 'utf-8').read()

        parser = HTML2Text()
        parser.feed(input_)
        self.assertEqual(parser.gettext(), expected_)

def suite():
    suite = unittest.TestSuite()

    for input_filename in glob.glob1(input_path, '*.html'):
        root, extension = os.path.splitext(input_filename)

        test = ParsingTest(root,
                           os.path.join(input_path, input_filename),
                           os.path.join(expected_path, '%s.txt' % root))

        suite.addTest(test)

    return suite
