import urlparse

from oauthlib.oauth1 import Client


def safe_unicode(s):
    # workaround for unicode requirements
    if isinstance(s, str):
        return unicode(s)
    return s


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

    def setClient(self, pmr2_client):
        self.pmr2_client = pmr2_client

    def hasAccess(self):
        return False


class BasicCredential(Credential):

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def getAuthorization(self, request):
        return 'Basic ' + ('%s:%s' %
            (self.username, self.password)).encode('base64').strip()

    def hasAccess(self):
        return not (self.username is None or self.password is None)


class OAuthCredential(Credential):

    REQUEST_TOKEN = 'OAuthRequestToken'
    AUTHORIZE_TOKEN = 'OAuthAuthorizeToken'
    GET_ACCESS_TOKEN = 'OAuthGetAccessToken'

    def __init__(self, client, access=None,
            callback=None, verifier=None):
        """
        The OAuth credential provider for PMR2 JSON Client.

        oauth_client
            The client key/secret pair.
        oauth_access
            The access key/secret pair.
        """

        self.client_key, self.client_secret = client
        # The reason why these are just simply called key/secret is due
        # to how they are reused for both temporary and access tokens.
        if access:
            self.key, self.secret = access
        else:
            self.clearAccess()

        self.callback = callback
        self.verifier = verifier

    def hasAccess(self):
        return not (self.key is None or self.secret is None)

    def clearAccess(self):
        self.key, self.secret = None, None

    def getAuthorization(self, request):
        client = Client(
            safe_unicode(self.client_key),
            safe_unicode(self.client_secret),
            safe_unicode(self.key),
            safe_unicode(self.secret),
            callback_uri=safe_unicode(self.callback),
            verifier=safe_unicode(self.verifier),
        )
        method = safe_unicode(request.get_method())
        url = safe_unicode(request.get_full_url())

        # data is omitted because no www-form-encoded data
        uri, headers, body = client.sign(url, method)
        return headers['Authorization']

    def getTemporaryCredential(self, callback=None, scope=None):
        if self.pmr2_client is None:
            raise ValueError('This PMR2 OAuth credential must be associated '
                'with a PMR2 instance before temporary credentials can be '
                'requested.')

        # Only clear access for temporary
        self.clearAccess()
        url = '%s/%s' % (self.pmr2_client.site, self.REQUEST_TOKEN)
        if scope:
            # it is better use an url builder of sort.
            url = '%s?scope=%s' % (url, scope)

        self.verifier = None
        if callback:
            self.callback = callback

        request = self.pmr2_client.buildRequest(url)
        fp = self.pmr2_client.open(request)
        rawstr = fp.read()
        fp.close()
        d = urlparse.parse_qs(rawstr)
        self.key = d.get('oauth_token', ['']).pop()
        self.secret = d.get('oauth_token_secret', ['']).pop()

    def getAccessCredential(self, verifier=None):
        if self.pmr2_client is None:
            raise ValueError('This PMR2 OAuth credential must be associated '
                'with a PMR2 instance before access credentials can be '
                'requested.')

        # Assume self.key is a request token key.
        url = '%s/%s' % (self.pmr2_client.site, self.GET_ACCESS_TOKEN)

        self.callback = None
        if verifier:
            self.verifier = verifier

        request = self.pmr2_client.buildRequest(url)
        fp = self.pmr2_client.open(request)
        rawstr = fp.read()
        fp.close()
        d = urlparse.parse_qs(rawstr)
        self.key = d.get('oauth_token', ['']).pop()
        self.secret = d.get('oauth_token_secret', ['']).pop()
        # do NOT include a verifier with a normal acces request as this
        # is an undefined behavior.  Will fail in the case of pmr2.oauth
        # as oauthlib will verify this if this value is supplied.
        self.verifier = None

    def getOwnerAuthorizationUrl(self):
        """
        Assume key is a temporary credential, use it to get the url to
        pass it to a resource owner.
        """

        return '%s/%s?oauth_token=%s' % (
            self.pmr2_client.site, self.AUTHORIZE_TOKEN, self.key)
