import urllib2
from cStringIO import StringIO

from Zope2.App import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
from Products.PloneTestCase.layer import onteardown

from pmr2.json.tests import base

from pmr2.jsonclient.client import PMR2Client
from Testing.testbrowser import PublisherHTTPHandler


@onsetup
def setup():
    # Inject the test opener.
    PMR2Client._opener = urllib2.build_opener(PublisherHTTPHandler)

setup()
