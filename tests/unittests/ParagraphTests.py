#!/usr/bin/python

import unittest
import sys
import os

import ParsingTests

class ParagraphTests(ParsingTests.ParsingTest):
    def testWellFormedParagraphs(self):
       return self.runParsingTest("multiparagraph-wellformed") 

def suite():
    suite = unittest.TestSuite()
    suite.addTest(ParagraphTests("testWellFormedParagraphs"))
    return suite

if __name__ == "__main__":
    unittest.main()
