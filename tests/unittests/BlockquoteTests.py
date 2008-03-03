#!/usr/bin/python

import unittest
import sys
import os

import ParsingTests

class BlockquoteTests(ParsingTests.ParsingTest):
    def testWellFormedBlockquote(self):
       return self.runParsingTest("blockquote") 

def suite():
    suite = unittest.TestSuite()
    suite.addTest(BlockquoteTests("testWellFormedBlockquote"))
    return suite

if __name__ == "__main__":
    unittest.main()
