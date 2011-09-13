import doctest
import unittest

#from zope.testing import doctestunit
#from zope.component import testing
from Testing import ZopeTestCase as ztc

from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Products.Five import fiveconfigure, zcml

ptc.setupPloneSite()

import collective.autosaveform

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


class AutoSaveFormTestCase(ptc.PloneTestCase):

    class layer(PloneSite):

        @classmethod
        def setUp(cls):
            fiveconfigure.debug_mode = True
            ztc.installPackage(collective.autosaveform)
            fiveconfigure.debug_mode = False

        @classmethod
        def tearDown(cls):
            pass

    def install_product(self):
        fiveconfigure.debug_mode = True
        zcml.load_config('configure.zcml',
                         collective.autosaveform)
        ztc.installPackage(collective.autosaveform)
        self.addProfile('collective.autosaveform:default')
        self.addProduct('collective.autosaveform')

class AutoSaveFormFunctionnalTestCase(AutoSaveFormTestCase,
                                      ptc.FunctionalTestCase):
    pass
