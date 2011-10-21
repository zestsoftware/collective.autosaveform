import unittest
from zope.testing import doctest

from collective.autosaveform.tests.base import OPTIONFLAGS

def test_suite():
    return unittest.TestSuite(
        [doctest.DocTestSuite(module='collective.autosaveform.utils',
                              optionflags=OPTIONFLAGS)])
