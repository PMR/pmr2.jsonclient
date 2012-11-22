import doctest
import unittest

from zope.component import testing
from Testing import ZopeTestCase as ztc

from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Products.PloneTestCase.layer import onsetup

from pmr2.jsonclient.tests import base


def test_suite():
    return unittest.TestSuite([

        ztc.ZopeDocFileSuite(
            'README.rst', package='pmr2.jsonclient',
            test_class=base.JsonClientTestCase,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
        ),

    ])
