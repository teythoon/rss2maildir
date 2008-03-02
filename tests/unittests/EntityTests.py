#!/usr/bin/python

import unittest
import os

import ParsingTests

class EntityTests(ParsingTests.ParsingTest):
    def testEntities(self):
        return self.runParsingTest("entities")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(SpacingTests("testEntities"))
    return suite

if __name__ == "__main__":
    unittest.main()
