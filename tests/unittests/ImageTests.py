#!/usr/bin/python

import unittest
import os

import ParsingTests

class ImageTests(ParsingTests.ParsingTest):
    def testBasicImage(self):
        return self.runParsingTest("image-test")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(ImageTests("testBasicImage"))
    return suite

if __name__ == "__main__":
    unittest.main()
