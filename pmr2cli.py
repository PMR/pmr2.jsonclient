import os.path
import time
import ConfigParser
import urllib2
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
DEFAULT_SCOPE = 'http://localhost:8280/pmr/scope/workspace_all'

HOME = os.path.expanduser('~')
CONFIG_FILENAME = os.path.join(HOME, '.pmr2clirc')


class PMR2Cli(object):

    token_key = ''
    token_secret = ''
    active = False
    debug = False

    def __init__(self, 
            pmr2root=PMR2ROOT,
            consumer_key=CONSUMER_KEY, 
            consumer_secret=CONSUMER_SECRET):

        self.credential = OAuthCredential(
            client=(consumer_key, consumer_secret))
        self.client = PMR2Client(pmr2root)
        self.client.setCredential(self.credential)

    def load_config(self, filename=CONFIG_FILENAME):
        config = ConfigParser.SafeConfigParser({
                'token_key': '',
                'token_secret': '',
                'debug': False,
            },
            allow_no_value=True,
        )
        config.read(filename)
        try:
            self.credential.key = config.get('main', 'token_key')
            self.credential.secret = config.get('main', 'token_secret')
            self.debug = config.getboolean('main', 'debug')
        except:
            # I don't care, I am not trapping each of the above in its
            # own exception for even just a missing value.
            print "Error reading configuration, rewriting."
            self.save_config()

    def save_config(self, filename=CONFIG_FILENAME):
        config = ConfigParser.ConfigParser()
        config.add_section('main')
        config.set('main', 'token_key', self.credential.key)
        config.set('main', 'token_secret', self.credential.secret)
        config.set('main', 'debug', self.debug)
        with open(filename, 'wb') as configfile:
            config.write(configfile)

    def get_access(self):
        # get user to generate one.
        self.credential.getTemporaryCredential(callback='oob')
        target = self.credential.getOwnerAuthorizationUrl()
        webbrowser.open(target)
        verifier = raw_input('Please enter the verifier: ')
        self.credential.getAccessCredential(verifier=verifier)

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

    def do_dashboard(self, *a):
        """
        List out the features available on the dashboard.
        """

        for i in self.client.getDashboard():
            print '"%s"\t%s' % (i['label'], i['target'])

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

    def shell(self):
        while self.active:
            try:
                raw = raw_input('> ')
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
        try:
            self.load_config()
        except ConfigParser.NoSectionError:
            pass

        client = PMR2Client(PMR2ROOT)
        if not self.credential.key and not self.credential.secret:
            try:
                self.get_access()
            except urllib2.HTTPError, e:
                print 'Fail to validate the verifier.'
                return
            self.save_config()

        try:
            self.client.updateDashboard()
        except urllib2.HTTPError, e:
            print 'Credentials are invalid and are purged.  Quitting'
            self.credential.key = ''
            self.credential.secret = ''
            self.save_config()
            return

        self.active = True
        print 'Starting PMR2 Demo Shell...'
        self.shell()

    def test(self):
        method = client.getDashboardMethod('workspace-add')


if __name__ == '__main__':
    cli = PMR2Cli()
    cli.run()
