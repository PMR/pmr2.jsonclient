import json
import os.path
import code
import time
import urllib2
from urllib import quote_plus
import readline
import traceback
import webbrowser

from pmr2.jsonclient import PMR2Client, OAuthCredential

# There are no settings for these.  Manually fill this out here with the
# consumer key and secret registered for this at the target PMR2ROOT.
# PMR2ROOT = 'https://models.physiomeproject.org'
PMR2ROOT = 'http://localhost:8280/pmr'
CONSUMER_KEY = 'XeGlniKGlGGYRyoChwygbgYC'
CONSUMER_SECRET = '55yxsmcV124kSsJInMhtsJl7'
DEFAULT_SCOPE = quote_plus(
    'http://localhost:8280/pmr/scope/collection,'
    'http://localhost:8280/pmr/scope/search,'
    'http://localhost:8280/pmr/scope/workspace_full'
)

HOME = os.path.expanduser('~')
CONFIG_FILENAME = os.path.join(HOME, '.pmr2clirc')


class PMR2Cli(object):

    token_key = ''
    token_secret = ''
    active = False
    scope = DEFAULT_SCOPE
    method = None
    _debug = 0

    def __init__(self, 
            pmr2root=PMR2ROOT,
            consumer_key=CONSUMER_KEY, 
            consumer_secret=CONSUMER_SECRET):

        self.credential = OAuthCredential(
            client=(consumer_key, consumer_secret))
        self.client = PMR2Client(pmr2root)
        self.client.setCredential(self.credential)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        if isinstance(value, int):
            self._debug = value

        if isinstance(value, basestring):
            if value.lower() in ('false', 'no', '0',):
                self._debug = 0
            else:
                self._debug = 1

    def build_config(self):
        return  {
            'token_key': self.credential.key,
            'token_secret': self.credential.secret,
            'debug': self.debug,
            'scope': DEFAULT_SCOPE,
        }

    def load_config(self, filename=CONFIG_FILENAME):
        try:
            fd = open(filename, 'r')
            config = json.load(fd)
            fd.close()
        except IOError:
            print "Fail to open configuration file."
            config = self.build_config()
        except ValueError:
            print "Fail to decode JSON configuration.  Using default values."
            config = self.build_config()

        self.credential.key = config.get('token_key', '')
        self.credential.secret = config.get('token_secret', '')
        self.debug = config.get('debug', 0)
        self.scope = config.get('scope', DEFAULT_SCOPE)

    def save_config(self, filename=CONFIG_FILENAME):
        try:
            fd = open(filename, 'wb')
            json.dump(self.build_config(), fd)
            fd.close()
        except IOError:
            print "Error saving configuration"

    def get_access(self):
        # get user to generate one.
        scope = self.scope
        try:
            self.credential.getTemporaryCredential(callback='oob', scope=scope)
        except urllib2.HTTPError, e:
            print 'Fail to request temporary credentials.'
            return
        target = self.credential.getOwnerAuthorizationUrl()
        webbrowser.open(target)
        verifier = raw_input('Please enter the verifier: ')
        self.credential.getAccessCredential(verifier=verifier)
        return True

    def do_help(self, *a):
        """
        Print this message.
        """

        print 'Basic demo commands:'
        print ''
        for name in sorted(dir(self)):
            if not name.startswith('do_'):
                continue
            obj = getattr(self, name)
            if not callable(obj):
                continue
            print name[3:]
            print obj.__doc__

    def do_console(self, *a):
        """
        Start the interactive python console.
        """

        console = code.InteractiveConsole(locals=locals())
        result = console.interact('')

    def do_dashboard(self, *a):
        """
        List out the features available on the dashboard.
        """

        dashboard = self.client.getDashboard()
        if not a:
            for k, v in dashboard.items():
                print '%s\t%s\t%s' % (k, v['label'], v['target'])
            return

        self.method = self.client.getDashboardMethod(a[0])
        print 'Acquired method "%s"; use console to interact.' % a[0]

    def do_list_workspace(self, *a):
        """
        Returns a list of workspaces within your private workspace
        container.
        """

        method = self.client.getDashboardMethod('workspace-home')
        for i in method.raw():
            print '"%s"\t%s' % (i['title'], i['target'])

    def do_raw(self, *a):
        """
        Open a target URL to receive raw API output.
        """

        print self.client.getResponse(''.join(a))

    def do_property(self, *a):
        """
        Set property for this object.
        """

        permitted = ['debug']

        if len(a) < 1:
            print "need both key and values."
            return

        args = list(a)
        prop = args.pop(0)

        if len(a) < 2:
            print '%s = %s' % (prop, getattr(self, prop))
            return

        if prop not in permitted:
            print "'%s' cannot be set" % prop
            return

        setattr(self, prop, ' '.join(args))

    def shell(self):
        while self.active:
            try:
                raw = raw_input('pmr2cli> ')
                if not raw:
                    continue
                rawargs = raw.split()
                command = rawargs.pop(0)
                obj = getattr(self, 'do_' + command, None)
                if callable(obj):
                    obj(*rawargs)
                else:
                    print "Invalid command, try 'help'."
            except EOFError:
                self.active = False
                print ''
            except KeyboardInterrupt:
                print '\nGot interrupt signal.'
                self.active = False
            except urllib2.HTTPError, e:
                print 'Server responded with error code %d' % e.code
            except:
                print traceback.format_exc()
                if self.debug:
                    import pdb;pdb.post_mortem()

    def run(self):
        self.load_config()

        client = PMR2Client(PMR2ROOT)
        access = False
        if not self.credential.hasAccess():
            try:
                access = self.get_access()
            except urllib2.HTTPError, e:
                print 'Fail to validate the verifier.'
        else:
            access = True

        if not access:
            self.save_config()
            return

        try:
            self.client.updateDashboard()
        except urllib2.HTTPError, e:
            print 'Credentials are invalid and are purged.  Quitting'
            self.credential.key = None
            self.credential.secret = None
            self.scope = DEFAULT_SCOPE
            self.save_config()
            return

        self.active = True
        print 'Starting PMR2 Demo Shell...'
        self.save_config()
        self.shell()

    def test(self):
        method = client.getDashboardMethod('workspace-add')


if __name__ == '__main__':
    cli = PMR2Cli()
    cli.run()
