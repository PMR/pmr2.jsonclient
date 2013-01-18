import urlparse

from oauthlib.oauth1 import Client


class Credential(object):
    """
    Credential to access a site.  Ideally this should all integrate
    somehow with urllib2.
    """

    pmr2_client = None

    def getAuthorization(self, request):
        """
        Subclass will implement the method to return the authorization
        header.
        """

        raise NotImplementedError()

    def apply(self, request):
        auth = self.getAuthorization(request)
        if auth:
            request.add_header('Authorization', auth)

    def setPMR2Client(self, pmr2_client):
        self.pmr2_client = pmr2_client


class BasicCredential(Credential):

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def getAuthorization(self, request):
        return 'Basic ' + ('%s:%s' %
            (self.username, self.password)).encode('base64').strip()


class OAuthCredential(Credential):

    REQUEST_TOKEN = 'OAuthRequestToken'
    AUTHORIZE_TOKEN = 'OAuthAuthorizeToken'
    GET_ACCESS_TOKEN = 'OAuthGetAccessToken'

    def __init__(self, client_key, access_key):
        self.client_key = client_key
        self.access_key = access_key

    def getAuthorization(self, *a, **kw):
        pass
