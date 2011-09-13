import unittest
from Testing import ZopeTestCase as ztc

from collective.autosaveform.tests.base import AutoSaveFormTestCase

def test_suite():
    return unittest.TestSuite([
        ztc.ZopeDocFileSuite(
           'tool.txt',
            package='collective.autosaveform.tests',
           test_class=AutoSaveFormTestCase),
        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
