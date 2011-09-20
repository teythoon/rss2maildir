#!/usr/bin/python

import sys
import unittest
import os

basedir = os.path.realpath(os.path.dirname(__file__))
unittestsdir = os.path.join( \
    basedir, \
    "unittests")

sys.path.insert(0, os.path.join(basedir, '..'))

unittestmodules = []

fullsuite = unittest.TestSuite()

# walk our directory tree looking for any modules available
for root, dir, files in os.walk(unittestsdir):
    for file in files:
        if file[-3:] == ".py" and file != "__init__.py":
            moduleinfo = ".".join(root[len(basedir)+1:].split(os.sep))
            unittestmodules.append(".".join((moduleinfo, file[0:-3])))

# run through the found modules and look for test suites
for unittestmodule in unittestmodules:
    # try importing the test and getting the suite
    try:
        suite_func = getattr(__import__(unittestmodule, {}, {}, ['']), "suite")
        # add the suite to the tests
        fullsuite.addTest(suite_func())
    except:
        # there was not test suite in there to run, skip it
        pass

testrunner = unittest.TextTestRunner()
testrunner.run(fullsuite)
