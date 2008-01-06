#!/usr/bin/python

import unittest
import sys
import os

import ParsingTests

class NestedListTests(ParsingTests.ParsingTest):
    def testWellFormedNestedLists(self):
        return self.runParsingTest("nestedlists-wellformed")

    def testWellFormedNestedOrderedLists(self):
        return self.runParsingTest("nestedorderedlists-wellformed")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(NestedListTests("testWellFormedNestedLists"))
    suite.addTest(NestedListTests("testWellFormedNestedOrderedLists"))
    return suite

if __name__ == "__main__":
    unittest.main()
