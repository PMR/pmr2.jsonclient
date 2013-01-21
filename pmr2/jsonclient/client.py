import json
import urllib2

import oauthlib

_protocol = 'application/vnd.physiome.pmr2.json.0'
_ua = 'PMR2Client/0.1'


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

    def __init__(self, site, credential=None):
        self.site = site
        self.credential = credential
        self.mismatched_content = None
    
    def buildRequest(self, url, data=None, headers=None):

        if data and not isinstance(data, basestring):
            data = json.dumps(data)

        if headers is None:
            headers = {}
        request = urllib2.Request(url, data=data, headers=headers)

        if self.credential:
            self.credential.apply(request)

        return request

    def open(self, request, trail=None):
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
            self.mismatched_content = fp.read()
            fp.close()
            raise ValueError('Content-Type mismatch')

        result = json.load(fp)
        fp.close()
        return result

    def setSite(self, site):
        self.site = site
        self.updateDashboard()

    def setCredential(self, credential, update=False):
        # XXX figure out some way to do the update smartly, such as test
        # whether the credentials are ready to be used.
        self.credential = credential
        self.credential.setPMR2Client(self)
        if update:
            self.updateDashboard()

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
