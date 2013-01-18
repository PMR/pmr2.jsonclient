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
the list of features for that particular instance of PMR2::

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
