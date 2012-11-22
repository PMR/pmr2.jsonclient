import urllib2
from cStringIO import StringIO

import zope.component
from Zope2.App import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
from Products.PloneTestCase.layer import onteardown
from Testing.testbrowser import PublisherHTTPHandler

from pmr2.jsonclient.client import PMR2Client, build_opener

from pmr2.testing.base import TestRequest
from pmr2.oauth.tests import base
from pmr2.json.tests import base
from pmr2.app.workspace.tests.base import WorkspaceDocTestCase


@onsetup
def setup():
    # Inject the test opener.
    PMR2Client._opener = build_opener(PublisherHTTPHandler)

@onteardown
def teardown():
    pass

setup()
teardown()
ptc.setupPloneSite(products=('pmr2.oauth',))


class JsonClientTestCase(WorkspaceDocTestCase):

    def afterSetUp(self):
        super(JsonClientTestCase, self).afterSetUp()
        request = TestRequest()

        from Products.PloneTestCase.setup import default_user
        from pmr2.oauth.interfaces import IConsumerManager, ITokenManager
        from pmr2.oauth.interfaces import IScopeManager
        from pmr2.oauth.consumer import Consumer
        from pmr2.oauth.token import Token

        # assuming none of these are overridden.
        self.consumer = Consumer('test.example.com', 'consumer-secret')
        cm = zope.component.getMultiAdapter((self.portal, request),
            IConsumerManager)
        cm.add(self.consumer)

        token = Token('pmr2token', 'token-secret')
        token.access = True
        token.consumer_key = self.consumer.key
        token.user = default_user

        self.token = token
        tm = zope.component.getMultiAdapter((self.portal, request), 
            ITokenManager)
        tm.add(self.token)

        # XXX especially this one.
        sm = zope.component.getMultiAdapter((self.portal, request),
            IScopeManager)
        sm.permitted = '^.*$'  # permit everything.
