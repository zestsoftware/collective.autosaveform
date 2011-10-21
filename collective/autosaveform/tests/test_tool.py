import unittest
from zope.testing import doctest
from Testing import ZopeTestCase as ztc

from collective.autosaveform.tests.base import AutoSaveFormTestCase, OPTIONFLAGS

def test_suite():
    return unittest.TestSuite([
        ztc.ZopeDocFileSuite(
           'tool.rst',
            package='collective.autosaveform.tests',
            optionflags=OPTIONFLAGS,
            test_class=AutoSaveFormTestCase),

        doctest.DocTestSuite(
            module='collective.autosaveform.utils',
            optionflags=OPTIONFLAGS)
        ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
