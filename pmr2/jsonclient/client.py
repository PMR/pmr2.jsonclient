import json
import urllib2

import oauth2 as oauth

_protocol = 'application/vnd.physiome.pmr2.json.0'
_ua = 'PMR2Client/0.1'

REQUEST_TOKEN = 'OAuthRequestToken'
AUTHORIZE_TOKEN = 'OAuthAuthorizeToken'
GET_ACCESS_TOKEN = 'OAuthGetAccessToken'


def build_opener(*handlers):
    result = urllib2.build_opener(*handlers)
    result.addheaders = [
        ('Accept', _protocol),
        ('Content-Type', _protocol),
        ('User-Agent', _ua),
    ]
    return result


class PMR2Client(object):

    _opener = build_opener()

    site = None
    _auth = None
    lasturl = None

    consumer = None
    token = None
    request_token = None

    dashboard = None

    def __init__(self, site):
        self.setSite(site)
        self.oauth_signature_method = oauth.SignatureMethod_HMAC_SHA1()
    
    def buildRequest(self, url, data=None, headers=None):

        if data and not isinstance(data, basestring):
            data = json.dumps(data)

        if headers is None:
            headers = {}
        request = urllib2.Request(url, data=data, headers=headers)

        if data:
            # we will need to override this.
            request.add_header('Content-Type', _protocol)

        # It may be impossible to generate an auth string, so any
        # Authorization header specified will override this.
        if not headers and not (headers and 'Authorization' in headers):
            auth = self.getAuthorization(request.get_method(), url)
            if auth:
                request.add_header('Authorization', auth)

        return request

    def getAuthorization(self, method, url):
        if self._auth is not None:
            # Assume basic auth
            return self._auth

        if not self.token:
            return None

        auth = self.buildOAuthHeaders(method, url, self.consumer, self.token)
        return auth.get('Authorization', None)

    def buildOAuthHeaders(self, method, url, consumer, token, parameters=None):
        # not using shortcuts because the method casts all string types
        # stupidly and needlessly into unicode type.
        # oreq = oauth.Request.from_consumer_and_token(
        #     consumer, token, http_url=url, parameters=parameters)

        # do this the long way.
        oreq = oauth.Request()
        oreq.url = url
        oreq.method = method

        defaults = {
            'oauth_timestamp': oauth.Request.make_timestamp(),
            'oauth_nonce': oauth.Request.make_nonce(),
            'oauth_version': oauth.Request.version,
        }

        if parameters:
            defaults.update(parameters)

        defaults['oauth_consumer_key'] = consumer.key
        if token:
            defaults['oauth_token'] = token.key
            if token.verifier:
                defaults['oauth_verifier'] = token.verifier

        oreq.is_form_encoded = True  # disables outdated spec.
        oreq.update(defaults)
        self._kb1 = self.oauth_signature_method.signing_base(oreq, consumer, token)
        oreq.sign_request(self.oauth_signature_method, consumer, token)
        self._kb2 = self.oauth_signature_method.signing_base(oreq, consumer, token)
        headers = oreq.to_header()
        return headers

    def open(self, request, trail=None):
        # since the request is not OAuth aware, the Authorization header
        # will not be regenerated new URI, resulting in an invalid
        # signature.  Thus we do it here until an appropriate request 
        # class is provided.
        url = request.get_full_url()
        if trail is None:
            trail = []

        try:
            return self._opener.open(request)
        except urllib2.HTTPError, e:
            if e.url == url or url in trail:
                raise
            trail.append(url)
            # XXX data will be omitted because we can't be sure if we
            # can POST to the new target.
            new_request = self.buildRequest(e.url)
            return self.open(new_request, trail)

    def getResponse(self, url, data=None):
        request = self.buildRequest(url, data)
        fp = self.open(request)
        self.lasturl = fp.geturl()

        if fp.headers.get('Content-Type') != _protocol:
            # some kind of error?
            raise ValueError('Content-Type mismatch')

        result = json.load(fp)
        fp.close()
        return result

    def setSite(self, site):
        self.site = site
        self.updateDashboard()

    def setCredentials(self, basic=None, oauth=None):
        if oauth:
            self.consumer = oauth.get('consumer', None)
            self.token = oauth.get('token', None)

            if not self.consumer:
                raise ValueError('missing OAuth consumer')

            self._auth = None
            return

        login = basic.get('login', '')
        password = basic.get('password', '')
        if login or password:
            self._auth = 'Basic ' + ('%s:%s' % 
                (login, password)).encode('base64').strip()

    def updateDashboard(self):
        url = '%s/pmr2-dashboard' % self.site
        result = self.getResponse(url)
        self.dashboard = result

    def getDashboard(self):
        if self.dashboard is None:
            self.updateDashboard()
        return self.dashboard

    def getDashboardMethod(self, name):
        action = self.dashboard[name]
        # Can't have unicode.
        url = str(action['target'])
        response = self.getResponse(url)
        # Uhh this will have a reference to this object, maybe track
        # that somehow?
        return PMR2Method(self, self.lasturl, response)


class PMR2Method(object):

    def __init__(self, context, url, obj):
        self.context = context
        self._obj = obj
        self.url = url

    def raw(self):
        return self._obj

    def fields(self):
        return self._obj.get('fields', {})

    def actions(self):
        return self._obj.get('actions', {})

    def errors(self):
        fields = self.fields()
        errors = []
        for name, field in fields.iteritems():
            error = field.get('error', '')
            if error:
                errors.append((name, error))
        return errors

    def post(self, action, fields):
        data = {}
        data['actions'] = {action: '1'}
        data['fields'] = fields
        result = self.context.getResponse(self.url, data)
        self.__init__(self.context, self.context.lasturl, result)
        return result
