PMR2 JSON Web Client
====================

To begin accessing PMR2 using a web client, start by instantiating the
main client object::

    >>> from pmr2.jsonclient import credential
    >>> from pmr2.jsonclient import PMR2Client
    >>> client = PMR2Client(self.portal.absolute_url())

Dashboard
---------

The dashboard is the first thing the client should see, as it returns
the list of features for that particular instance of PMR2.  Have to call
the update method before it can be used::

    >>> result = client.updateDashboard()
    >>> result = client.getDashboard()
    >>> sorted(result['workspace-home'].items())
    [(u'label', u'List personal workspaces'),
    (u'target', u'http://nohost/plone/pmr2-dashboard/workspace-home')]
    >>> sorted(result['workspace-add'].items())
    [(u'label', u'Create personal workspace'),
    (u'target', u'http://nohost/plone/pmr2-dashboard/workspace-add')]

The helper method ``getDashboardMethod`` on one of the keys will
retrieve the description and construct the method wrapper class which is
used to interact with the associated PMR2 instance.  Let's try to add
a workspace::

    >>> method = client.getDashboardMethod('workspace-add')
    Traceback (most recent call last):
    ...
    ValueError: Content-Type mismatch

Looks like there are some problems.  The PMR2 jsonclient communicates
with the server using a custom mimetype, and if there are no errors PMR2
will return the content with the same mimetype set.  Sometimes problems
may occur and this is the result, and to aid debugging, the attribute
``mismatched_content`` will be set::

    >>> print client.mismatched_content
    <BLANKLINE>
    ...
    <label for="__ac_name">Login Name</label>
    <input type="text" size="15" name="__ac_name" value="" id="__ac_name" />
    ...

It appears the client has been redirected to a login page, as some form
of credentials must be provided to permit the adding of workspaces.

Basic Credentials
-----------------

Under normal circumstances, adding content to PMR2 requires some form of
credentials, and almost always they will come in the form of user name
and passwords.  This can be done like so::

    >>> from Products.PloneTestCase.setup import default_user, default_password
    >>> client.setCredential(credential.BasicCredential(
    ...     username=default_user,
    ...     password=default_password
    ... ))

However, if PMR2 functionality are to be used by third-parties on behalf
of its users, sharing of passwords poses certain security hazards, and
so for this use case OAuth must be used.  This requires a whole separate
workflow which will be documented later.

Again, ``BasicCredential`` is NOT the recommended method to use by
third-party applications to access a user's content on PMR2.

Workspace
---------

Currently the only method supported is the creation of workspaces. Fetch
the description of the add workspace method::

    >>> method = client.getDashboardMethod('workspace-add')
    >>> print method.url
    http://nohost/plone/w/test_user_1_/+/addWorkspace

List the fields::

    >>> fields = method.fields()
    >>> sorted(fields.keys())
    [u'description', u'id', u'storage', u'title']
    >>> print fields['description']['klass']
    textarea-widget text-field
    >>> storage = [i['value'] for i in fields['storage']['items']]
    >>> u'dummy_storage' in storage
    True

Then the actions::

    >>> actions = method.actions()
    >>> actions['add']
    {u'title': u'Add'}

Now execute the method using the add action::

    >>> response = method.post(action='add', fields={
    ...     'id': 'cake', 
    ...     'title': 'Tasty cake',
    ...     'description': 'This is a very tasty cake for testing',
    ...     'storage': 'dummy_storage',
    ... })

The workspace object should have been created::

    >>> self.portal.w.test_user_1_.cake
    <Workspace at /plone/w/test_user_1_/cake>
    >>> self.portal.w.test_user_1_.cake.description
    u'This is a very tasty cake for testing'

The method object will also act as a pointer to the newly created item,
and the response it gives can be retrieved like so::

    >>> method.url
    'http://nohost/plone/w/test_user_1_/cake'
    >>> raw = method.raw()
    >>> raw['id']
    u'cake'

On the other hand, if there is an error, the method will return a list
of errors.  Here we try to create the workspace using the same set of
parameters::

    >>> method = client.getDashboardMethod('workspace-add')
    >>> response = method.post(action='add', fields={
    ...     'id': 'cake', 
    ...     'title': 'Tasty cake',
    ...     'description': 'This is a very tasty cake for testing',
    ...     'storage': 'dummy_storage',
    ... })

Now we should have a list of errors::

    >>> method.errors()
    [(u'id', u'The specified id is already in use.')]

We should be able to reuse the same method as it should still reference
the same url::

    >>> response = method.post(action='add', fields={
    ...     'id': 'test', 
    ...     'title': 'Tasty test',
    ...     'description': 'This is a very tasty test for testing',
    ...     'storage': 'dummy_storage',
    ... })
    >>> method.url
    'http://nohost/plone/w/test_user_1_/test'
    >>> raw = method.raw()
    >>> raw['description']
    u'This is a very tasty test for testing'

OAuth based credentials/authentication workflow
-----------------------------------------------

OAuth is the only recommended method to enable third-party access of a
user's content on PMR2.  The specifications for OAuth 1.0 is described
by `RFC5849`_, and this section terms from that document will be used.

.. _`RFC5849`: http://tools.ietf.org/html/rfc5849

While OAuth 2.0 is already finalized into `RFC6749`_ and deprecated
OAuth 1.0, oauthlib (the library that PMR2 uses to provide OAuth
support) only provides support for the draft specification for OAuth
2.0.  If this changes and a sufficiently mature implementation becomes
available, OAuth 1.0 will remain the only viable option for the mean
time.

.. _`RFC6749`: http://tools.ietf.org/html/rfc6749

For demonstration, a few assumptions and shortcuts will be taken and
shown.  The first one is that a client (consumer) key must be provided
by the PMR2 administrator to the client.  In this demonstration, first
create an OAuth credential object and assign it the key and secret of
the predefined client object::

    >>> cred = credential.OAuthCredential(
    ...     client=(self.consumer.key, self.consumer.secret),
    ... )

The object need to be assigned to a site before it can request for a
temporary credential::

    >>> cred.getTemporaryCredential()
    Traceback (most recent call last):
    ...
    ValueError: ...
    >>> (cred.key, cred.secret) == (None, None)
    True

Try this again after this credential object is set to a PMR2Client
object.  Also supply a callback, for we are testing this as an stand-
alone application, it will be set to ``oob``::

    >>> client = PMR2Client(self.portal.absolute_url())
    >>> client.setCredential(cred)
    >>> cred.getTemporaryCredential(callback='oob')
    >>> (cred.key, cred.secret) == (None, None)
    False

Now that the temporary credentials are present, direct the user to
visit the authorization page.  The URL can be retrieved using this
method::

    >>> target = cred.getOwnerAuthorizationUrl()

Users opens the target url::

    >>> self.user_browser.open(target)
    >>> self.user_browser.getControl(name="form.buttons.approve").click()

Naturally, temporary credentials cannot do anything, even if the user
had just approved the token.  Since OAuth credentials are provided, the
verification process should trigger on the temporary token and then fail
the request with an HTTP 403, rather than a redirect to the login page::

    >>> result = client.updateDashboard()
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 403: Forbidden

The user approved the token on the PMR2 instance, and then helpfully
submits the verifier on that page.  For ease of demonstration, this
helper method will do that here::

    >>> verifier = self.userSubmitVerifier(cred.key)

Now with the verifier, it is now possible to acquire the access token::

    >>> cred.getAccessCredential(verifier=verifier)

Then see if the access credentials are correctly assigned by trying to
retrieve the workspace-add method::

    >>> result = client.updateDashboard()
    >>> method = client.getDashboardMethod('workspace-add')
    >>> print method.url
    http://nohost/plone/w/test_user_1_/+/addWorkspace
