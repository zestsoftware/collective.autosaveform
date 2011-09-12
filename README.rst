collective.autosaveform
=======================

The goal of this product is to save what user entered in a form and
possibly repopulate the form when something bad happened (browser
crash, lost internet access etc).

If available, it stores data entered in the browser's local storage
and sends them to the server to copy them. If the local storage is not
available, it always sends the data to the server.
If a problem arise, the form will be prepopulated when the user opens
is again.

Installation
============

Add 'collective.autosaveform' to your list of eggs in the
buildout. Run buildout again, then install it using Zope quick
installer (or Plone product managment).

Sample
======

A form sample can be found at this address:

  http://localhost:8080/<yourplonesite>/autosave_sample


Setting up forms
================

To enable auto saving of a form, you first need to add an ID to your
form::

  <form id="my_saved_form">
  </form>

Then, you have to register it on the Python side. This can be done via
an upgrade step for example::

  from collective.autosaveform import config
  from Products.CMFCore.utils import getToolByName

  def register_form(context):
      tool = getToolByName(context, 'portal_autosaveform')
      try:
          tool.register_form('my_saved_form',
                             {'text_field': config.TEXT,
                              'radio_field': config.RADIO})
      except:
          # Log that the form was already registered.
	  pass

When you process the form, you should also mark it as processed (so
the data will not be filled again)::

  def process_form(...):
      # Process the form ...
      tool = getToolByName(context, 'portal_autosaveform')
      tool.mark_form_processed('my_saved_form')

    

Last step, in the template where your form is located, enable the
jQuery plugin to have your form automatically saved::

  <script type="text/javascript">
    jq('#my_saved_form').autosaveform();
  </script>

You can have a look at the jQuery plugin for available options
(collective/autosaveform/skins/autosaveform/jquery.autosaveforms.js).
