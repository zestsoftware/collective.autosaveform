import unittest
from Testing import ZopeTestCase as ztc
from Testing.ZopeTestCase import FunctionalDocFileSuite

from collective.autosaveform.tests.base import AutoSaveFormFunctionnalTestCase, OPTIONFLAGS

def test_suite():
    return unittest.TestSuite([
        FunctionalDocFileSuite(
           'browser.rst',
            package='collective.autosaveform.tests',
            optionflags=OPTIONFLAGS,
            test_class=AutoSaveFormFunctionnalTestCase),
        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
