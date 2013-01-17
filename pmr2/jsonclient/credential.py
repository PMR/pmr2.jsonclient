import oauthlib


class Credential(object):
    """
    Credential to access a site.  Ideally this should all integrate
    somehow with urllib2.
    """

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


class BasicCredential(Credential):

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def getAuthorization(self, request):
        return 'Basic ' + ('%s:%s' %
            (self.username, self.password)).encode('base64').strip()


class OAuthCredential(Credential):

    def __init__(self, client_key, access_key):
        self.client_key = client_key
        self.access_key = access_key

    def getAuthorization(self, method, url):
        raise NotImplementedError()
