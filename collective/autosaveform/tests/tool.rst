portal_autosaveform tests
=========================

Setup
-----

We need to do some mocking, as displaying persistent objects is not
that efficient::

    >>> from persistent.dict import PersistentDict
    >>> PersistentDict.__old__str__ = PersistentDict.__str__
    >>> PersistentDict.__str__ = lambda x: '{%s}' % ', '.join(['%s: %s' % (k, v)
    ...                                                        for k, v in x.items()])
    >>> PersistentDict.__old__repr__ = PersistentDict.__repr__
    >>> PersistentDict.__repr__ = lambda x: x.__str__()

    >>> from persistent.list import PersistentList
    >>> PersistentList.__old__str__ = PersistentList.__str__
    >>> PersistentList.__str__ = lambda x: '[%s]' % ', '.join(x)
    >>> PersistentList.__old__repr__ = PersistentList.__repr__
    >>> PersistentList.__repr__ = lambda x: x.__str__()


Getting the tool is done by using ``getToolByName``::

    >>> self.install_product()
    >>> from Products.CMFCore.utils import getToolByName
    >>> tool = getToolByName(self.portal, 'portal_autosaveform')
    >>> tool
    <AutoSaveFormTool at /plone/portal_autosaveform>

Registering forms
-----------------

We have not registered any form yet, so all lists are empty::

    >>> tool._get_forms_list()
    {}
    >>> tool._get_saved_values()
    {}
    >>> tool._get_saved_versions()
    {}
    >>> tool._get_processed_forms()
    {}

We'll register one form::

    >>> from collective.autosaveform import config
    >>> tool.register_form('my_form', {'a_text_field': config.TEXT,
    ...                                'a_checkbox_field': config.CHECKBOX})


    >>> tool._get_forms_list()
    {my_form: {fields: {a_text_field: 0, a_checkbox_field: 1}}}
    >>> tool._get_saved_values()
    {}
    >>> tool._get_saved_versions()
    {}
    >>> tool._get_processed_forms()
    {}

If we try to register the form a second time, we get an error::

    >>> tool.register_form('my_form', {'a_text_field': config.TEXT,
    ...                                'a_checkbox_field': config.CHECKBOX})
    Traceback (most recent call last):
    ...
    IndexError: A form is already registered with id "my_form"

Fields for a form can be updated using the ``update_form_fields`` method::

    >>> tool.update_form_fields('my_form', {'a_text_field': config.TEXT,
    ...                                     'a_new_field': config.RADIO})
    >>> tool._get_forms_list()
    {my_form: {fields: {a_new_field: 2, a_text_field: 0}}}

    >>> tool.get_form_fields('my_form')
    {'a_new_field': 2, 'a_text_field': 0}


Saving and getting values
-------------------------

We now have our form registered, so we can save some values in it::

    >>> tool.save_form('my_form', 'some_user', 1, {'a_text_field': 'Hello world',
    ...                                            'a_new_field': 'A value'})


If we try to save values for a form than is not registered, we get an error::

    >>> tool.save_form('my_unknown_form', 'some_user', 1, {'a_text_field': 'Hello world',
    ...                                                    'a_new_field': 'A value'})
    Traceback (most recent call last):
    ...
    IndexError: Unknown id "my_unknown_form": this form has not been registered


Once values have been saved, we can get some info about the
form. First the values that have been saved::

    >>> tool.load_form('my_form', 'some_user')
    {'a_new_field': 'A value', 'a_text_field': 'Hello world'}

If we try to load data for an unregistered form or for a user that did
not yet save info, we get an empty dictionary::

    >>> tool.load_form('my_unregistered_form', 'some_user')
    {}
    
    >>> tool.load_form('my_form', 'another_user')
    {}

We can also get the latest version of the saved values::

    >>> tool.get_saved_version('my_form', 'some_user')
    1

When trying to get version for an unregistered form or a user that has
not yet saved data, we get -1::

    >>> tool.get_saved_version('my_unregistered_form', 'some_user')
    -1

    >>> tool.get_saved_version('my_form', 'another_user')
    -1


We can also check if the form has already been processed. This is used
to know if we should repopulate the form or not::

    >>> tool.is_form_processed('my_form', 'some_user')
    False

It also returns False for unregistered forms and user that did not
save values yet::

    >>> tool.is_form_processed('my_unregistered_form', 'some_user')
    False

    >>> tool.is_form_processed('my_form', 'another_user')
    False

To get a positive answer, we have to mark the form as processed::

    >>> tool.register_form('a_second_form', {})
    >>> tool.is_form_processed('a_second_form', 'my_user')
    False
    >>> tool.mark_form_processed('a_second_form', 'my_user')
    >>> tool.is_form_processed('a_second_form', 'my_user')
    True

A form can be saved multiple times, only the lastest entries will be saved::

    >>> tool.save_form('my_form', 'some_user', 2, {'a_text_field': 'bla',
    ...                                            'a_new_field': 'bli'})
    >>> tool.save_form('my_form', 'some_user', 3, {'a_text_field': 'bla1',
    ...                                            'a_new_field': 'bli1'})
    >>> tool.save_form('my_form', 'some_user', 4, {'a_text_field': 'bla2',
    ...                                            'a_new_field': 'bli2'})

    >>> tool.get_saved_version('my_form', 'some_user')
    4
    >>> tool.load_form('my_form', 'some_user')
    {'a_new_field': 'bli2', 'a_text_field': 'bla2'}

