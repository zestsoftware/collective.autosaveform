Views tests
===========

The browser views added by collective.autosaveforms are mainly Ajax
views. We can not directly test the effects on the browser (as it does
not emulate JS), so we'll just test that the data sent are correct.

Setup
-----

Install collective.autosaveform and get a working browser::

    >>> self.install_product()
    >>> from Products.Five.testbrowser import Browser
    >>> browser = Browser()

We create a simple method to handle POST data sent to the Ajax
views. Our views do not really care if it gets POST or GET data
hopefully::

    >>> def make_url(view_name, data):
    ...     def make_value(key, value):
    ...         if isinstance(value, list):
    ...             return '&'.join([make_value(key, v) for v in value])
    ...         return '%s=%s' % (key, value)
    ...     
    ...     return '%s/%s?%s' % ('http://nohost/plone',
    ...                          view_name,
    ...                          '&'.join([make_value(k, v) for k, v in data.items()]))
    >>> make_url('my_view', {'single_arg': 12, 'list_arg': ['a', 'b', 'c']})
    'http://nohost/plone/my_view?single_arg=12&list_arg=a&list_arg=b&list_arg=c'

    >>> def send_data(view_name, data):
    ...     url = make_url(view_name, data)
    ...     browser.open(url)
    ...     return browser.contents

JS file installation
--------------------

When installing ``collective.autosaveforms``, a new JS file is added to
handle manipulations on client side::

    >>> browser.open('http://nohost/plone/')
    >>> page = browser.contents

We need to extract the JS file from the content (as Plone will
automatically compress it)::

    >>> import re
    >>> exp = r'http://nohost/plone/portal_javascripts/Plone%20Default/jquery.autosaveforms-cachekey\d+.js'
    >>> matches = re.findall(exp, page, re.MULTILINE)
    >>> matches
    ['http://nohost/plone/portal_javascripts/Plone%20Default/jquery.autosaveforms-cachekey....js']

    >>> browser.open(matches[0])
    >>> '$.fn.autosaveform = function(opts)' in browser.contents
    True

Registering the sample form
---------------------------

A sample form is provided with the product, it can be registered in
the system by calling the ``register_autosaveform_sample`` view::

    >>> send_data('register_autosaveform_sample', {})
    'Form registered'

We also need to be logged-in to be able to save our data::

    >>> from Products.PloneTestCase import PloneTestCase as ptc
    >>> browser.open('http://nohost/plone//login_form')
    >>> browser.getControl(name='__ac_name').value = ptc.portal_owner
    >>> browser.getControl(name='__ac_password').value = ptc.default_password
    >>> browser.getControl(name='submit').click()
    >>> 'You are now logged in' in  browser.contents
    True

Saving and getting values
-------------------------

The first method to test is ``jq_autosave_form_load``. It's a
jquery.pyproxy method (so the result needs to be processed by the package).
Currently, as we have not yet loaded any data, it just returns an
empty list of commands::

    >>> form_id = 'autosave_sample'
    >>> send_data('jq_autosave_form_load', {'form_id': form_id})
    '[]'


The method to load data is the only one using ``jquery.pyproxy``. The other
ones return plain JSON.
``jq_autosave_get_fields`` returns the list of fields registered for a
form with their type (based on collective.autosave.config definitions)::

    >>> send_data('jq_autosave_get_fields', {'form_id': form_id})
    '{"select_field": 3, "checkbox_field": 1, "textarea_field": 4, "radio_field": 2, "multi_checkbox_field": 1, "multi_select_field": 3, "text_field": 0}'

Results of this method do not change until we call the
``update_form_fields`` method of ``portal_autosaveforms``.

``jq_autosave_get_version`` returns the version of the form saved for
the user and a boolean telling if the user already processed this form::

    >>> send_data('jq_autosave_get_version', {'form_id': form_id})
    '{"version": -1, "processed": false}'

To save user inputs, we have to call the ``jq_autosave_form_save`` method::

    >>> send_data('jq_autosave_form_save', {'form_id': form_id,
    ...                                     'form_version': 1,
    ...                                     'text_field': 'Some text input',
    ...                                     'radio_field': 'radio2',
    ...                                     'checkbox_field': 'checkbox',
    ...                                     'multi_checkbox_field': ['checkbox2', 'checkbox3'],
    ...                                     'select_field': 'select4',
    ...                                     'multi_select_field': ['select1', 'select3'],
    ...                                     'textarea_field': 'A loooong test about thing and stuff'})
    ''

This views does not return anything, we have to call the view to load
a form to see if data have been saved correctly::

    >>> send_data('jq_autosave_form_load', {'form_id': form_id})
    '[{"args": ["selected", "selected"], "call": "attr", "selector": "#autosave_sample select[name=select_field] option[value=select4]"},
     {"args": ["checked", "checked"], "call": "attr", "selector": "#autosave_sample input[name=checkbox_field][value=checkbox]"},
     {"args": ["value", "A loooong test about thing and stuff"], "call": "attr", "selector": "#autosave_sample [name=textarea_field]"},
     {"args": ["checked", "checked"], "call": "attr", "selector": "#autosave_sample input[name=radio_field][value=radio2]"},
     {"args": ["checked", "checked"], "call": "attr", "selector": "#autosave_sample input[name=multi_checkbox_field][value=checkbox2]"},
     {"args": ["checked", "checked"], "call": "attr", "selector": "#autosave_sample input[name=multi_checkbox_field][value=checkbox3]"},
     {"args": ["selected", "selected"], "call": "attr", "selector": "#autosave_sample select[name=multi_select_field] option[value=select1]"},
     {"args": ["selected", "selected"], "call": "attr", "selector": "#autosave_sample select[name=multi_select_field] option[value=select3]"},
     {"args": ["value", "Some text input"], "call": "attr", "selector": "#autosave_sample [name=text_field]"}]'

This will be translated by the JS side of ``jquery.pyproxy`` into jQuery
calls to update the page content.

If we take a look at the view to get the form version, it should now
be updated::

    >>> send_data('jq_autosave_get_version', {'form_id': form_id})
    '{"version": "1", "processed": false}'

We can now process the form by clicking on the ``Process`` button of the form::

    >>> browser.open('http://nohost/plone/autosave_sample')
    >>> browser.getControl(name='process').click()

The form is now marked as processed::

    >>> send_data('jq_autosave_get_version', {'form_id': form_id})
    '{"version": "1", "processed": true}'

Note: calling the ``jq_autosave_get_version`` will mark again the form
as not-processed. The reason is that, if we call this view, that means
the user has opened the form again. So, we'll want to store data again::

    >>> send_data('jq_autosave_get_version', {'form_id': form_id})
    '{"version": "1", "processed": false}'

But the data of the form will have been wiped out::

    >>> send_data('jq_autosave_form_load', {'form_id': form_id})
    '[]'