PMR2 JSON Web Client
====================

To begin accessing PMR2 using a web client, start by instantiating the
main client object.
::

    >>> from pmr2.jsonclient import PMR2Client
    >>> client = PMR2Client()
    >>> client.setSite(self.portal.absolute_url())

Credentials
-----------

Add your basic authentication credentials (i.e. login/password).  This
will be deprecated as soon as OAuth is operational.
::

    >>> from Products.PloneTestCase.setup import default_user, default_password
    >>> client.setCredentials(basic=dict(
    ...     login=default_user,
    ...     password=default_password
    ... ))

Alternatively, OAuth authentication credentials (will be available once
implemented).
::

    >>> from oauth2 import Consumer, Token
    >>> consumer = Consumer('consumer.example.com', 'consumer-secret')
    >>> token = Token('pmr2token', 'token-secret')
    >>> client.setCredentials(oauth=dict(
    ...     consumer=consumer,
    ...     token=token,
    ... ))
    Traceback (most recent call last):
    ...
    NotImplementedError: ...
    ...

Dashboard
---------

The dashboard is the first thing the client should see, as it returns
the list of features for that particular instance of PMR2.
::

    >>> result = client.getDashboard()
    >>> sorted(result['workspace-home'].items())
    [(u'label', u'List personal workspaces'),
    (u'target', u'http://nohost/plone/pmr2-dashboard/workspace-home')]
    >>> sorted(result['workspace-add'].items())
    [(u'label', u'Create personal workspace'),
    (u'target', u'http://nohost/plone/pmr2-dashboard/workspace-add')]

Workspace
---------

Currently the only method supported is the creation of workspaces. Fetch
the description of the add workspace method.
::

    >>> method = client.getMethod('workspace-add')
    >>> print method.url
    http://nohost/plone/w/test_user_1_/+/addWorkspace

List the fields.
::

    >>> fields = method.fields()
    >>> sorted(fields.keys())
    [u'description', u'id', u'storage', u'title']
    >>> print fields['description']['klass']
    textarea-widget text-field
    >>> print [i['value'] for i in fields['storage']['items']]
    [u'dummy_storage']

Then the actions.
::

    >>> actions = method.actions()
    >>> actions['add']
    {u'title': u'Add'}

Now call the method.
::

    >>> response = method.call(action='add', fields={
    ...     'id': 'cake', 
    ...     'title': 'Tasty cake',
    ...     'description': 'This is a very tasty cake for testing',
    ...     'storage': 'dummy_storage',
    ... })
    >>> self.portal.w.test_user_1_.cake
    <Workspace at /plone/w/test_user_1_/cake>
