PMR2 JSON Web Client
====================

To begin accessing PMR2 using a web client, start by instantiating the
main client object::

    >>> from pmr2.jsonclient import credential
    >>> from pmr2.jsonclient import PMR2Client
    >>> client = PMR2Client(self.portal.absolute_url())

Credentials
-----------

Add your basic authentication credentials (i.e. login/password).  This
is not recommended for use within a typical client due to the security
issue of sharing of passwords::

    >>> from Products.PloneTestCase.setup import default_user, default_password
    >>> client.setCredential(credential.BasicCredential(
    ...     username=default_user,
    ...     password=default_password
    ... ))

Alternatively, OAuth authentication credentials (will be available once
implemented)::

    >>> import oauthlib

Should test for the whole process using the client helper classes, and
have the service provide a way to check for user name.

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

The helper method `getDashboardMethod` provides a shortcut to work with
the provided features.

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
