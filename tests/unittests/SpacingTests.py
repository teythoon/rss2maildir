#!/usr/bin/python

import unittest
import os

import ParsingTests

class SpacingTests(ParsingTests.ParsingTest):
    def testNormalisingSpacing(self):
        return self.runParsingTest("non-normalised-spacing")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(SpacingTests("testNormalisingSpacing"))
    return suite

if __name__ == "__main__":
    unittest.main()
