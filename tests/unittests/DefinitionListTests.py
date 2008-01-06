#!/usr/bin/python

import unittest
import os

import ParsingTests

class DefinitionListTests(ParsingTests.ParsingTest):
    def testWellFormedDefinitionList(self):
        return self.runParsingTest("definitionlist-wellformed")

    def testBadlyFormedDefinitionList(self):
        return self.runParsingTest("definitionlist-badlyformed")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(DefinitionListTests("testWellFormedDefinitionList"))
    suite.addTest(DefinitionListTests("testBadlyFormedDefinitionList"))
    return suite

if __name__ == "__main__":
    unittest.main()
