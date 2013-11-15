import urllib2
from cStringIO import StringIO

import zope.interface
import zope.component
from zope.annotation.interfaces import IAnnotatable, IAttributeAnnotatable
from plone.browserlayer.utils import register_layer

from Zope2.App import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
from Products.PloneTestCase.layer import onteardown
from Products.PloneTestCase.setup import default_user, default_password
from Testing.testbrowser import PublisherHTTPHandler
from Testing.testbrowser import Browser

from pmr2.testing.base import TestRequest as BaseTestRequest

from pmr2.oauth.scope import BaseScopeManager
from pmr2.oauth.interfaces import IConsumerManager, ITokenManager
from pmr2.oauth.interfaces import IScopeManager
from pmr2.oauth.consumer import Consumer, ConsumerManager
from pmr2.oauth.token import Token, TokenManager
from pmr2.oauth.factory import factory

from pmr2.app.workspace.tests.base import WorkspaceDocTestCase
from pmr2.app.interfaces import IPMR2AppLayer

from pmr2.oauth.tests import base  # trigger onsetup
from pmr2.json.tests import base  # trigger onsetup

from pmr2.jsonclient.client import Client, build_opener

@onsetup
def setup():
    # Inject the test opener.
    Client._opener = build_opener(PublisherHTTPHandler)

@onteardown
def teardown():
    pass

setup()
teardown()
ptc.setupPloneSite(products=('pmr2.oauth',))


class IPMR2JsonClientTestLayer(IPMR2AppLayer):
    """Json Test Layer"""


class TestRequest(BaseTestRequest):
    zope.interface.implements(IPMR2JsonClientTestLayer)


class MockScopeManager(BaseScopeManager):
    """
    Mock factory to disable scope.
    """

    zope.component.adapts(IAttributeAnnotatable, zope.interface.Interface)

    def getScope(self, key, default=None):
        return True

    def popScope(self, key, default=None):
        return True

    def setAccessScope(self, access_key, scope):
        return True

    def getAccessScope(self, access_key, default=None):
        return True

    def validate(self, *a, **kw):
        return True

    def requestScope(self, request_key, raw_scope):
        return True


class JsonClientTestCase(WorkspaceDocTestCase):

    def afterSetUp(self):
        super(JsonClientTestCase, self).afterSetUp()
        register_layer(IPMR2JsonClientTestLayer, 'pmr2.jsonclient.tests')
        request = TestRequest()

        # Ensure that the most basic scope managers are being used.
        cmf = factory(ConsumerManager)
        tmf = factory(TokenManager)
        smf = factory(MockScopeManager)

        zope.component.provideAdapter(
            cmf, (IAnnotatable, IPMR2JsonClientTestLayer,), IConsumerManager)
        zope.component.provideAdapter(
            tmf, (IAnnotatable, IPMR2JsonClientTestLayer,), ITokenManager)
        zope.component.provideAdapter(
            smf, (IAnnotatable, IPMR2JsonClientTestLayer,), IScopeManager)

        # assuming none of these are overridden.
        self.consumer = Consumer('test.example.com', 'consumer-secret',
            u'PMR2 Test JSON Client', None)
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

        b = Browser()
        portal_url = self.portal.absolute_url()
        b.open(portal_url + '/login')
        b.getControl(name='__ac_name').value = default_user
        b.getControl(name='__ac_password').value = default_password
        b.getControl(name='submit').click()
        self.user_browser = b

    def userSubmitVerifier(self, key):
        from pmr2.oauth.interfaces import ITokenManager
        request = TestRequest()
        tm = zope.component.getMultiAdapter((self.portal, request), 
            ITokenManager)
        token = tm.getRequestToken(key)
        return token.verifier
