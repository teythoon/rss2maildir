#!/usr/bin/python

import sys
import os
import glob
import unittest

basedir = os.path.realpath(os.path.dirname(__file__))
unittests_module = 'unittests'
unittests_path = os.path.join(basedir, unittests_module)

sys.path.insert(0, os.path.join(basedir, '..'))

unittestmodules = ['%s.%s' % (unittests_module, os.path.splitext(file_)[0])
                   for file_ in glob.glob1(unittests_path, '*.py')
                   if file_ != '__init__.py']

fullsuite = unittest.TestSuite()

# run through the found modules and look for test suites
for unittestmodule in unittestmodules:
    # try importing the test and getting the suite
    try:
        suite_func = getattr(__import__(unittestmodule, {}, {}, ['']), 'suite')
        # add the suite to the tests
    except:
        # there was not test suite in there to run, skip it
        continue
    fullsuite.addTest(suite_func())

testrunner = unittest.TextTestRunner()
testrunner.run(fullsuite)
