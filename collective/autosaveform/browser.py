from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
import simplejson as json

from jquery.pyproxy.plone import jquery, JQueryProxy

import config

class AutoSaveAjax(BrowserView):
    @property
    def autosave_tool(self):
        """ Return the tool created by the package.
        """
        return getToolByName(self.context, 'portal_autosaveform')

    @property
    def mtool(self):
        """ Returns the membership tool.
        """
        return getToolByName(aq_inner(self.context),
                             'portal_membership')

    def get_user_id(self):
        """ Returns current user id.
        Return None if the user is not logged in.
        """
        if self.mtool.isAnonymousUser():
            return
        user = self.mtool.getAuthenticatedMember()
        return user.id

    def get_fields(self):
        """ Returns a JSON dictionnary of all registered fields
        and associated type for the form identified by 'form_id'
        passed as a GET or POST parameter.
        """
        form = self.request.form
        form_id = form.get('form_id', None)

        if form_id is None:
            return

        try:
            return json.dumps(self.autosave_tool.get_form_fields(form_id))
        except IndexError:
            return

    def get_saved_version(self):
        """ Returns the saved version of the form identified by the 'form_id'
        GET/POST parameter.
        """
        form_id = self.request.form.get('form_id', None)
        user_id = self.get_user_id()
        if form_id:
            version = self.autosave_tool.get_saved_version(form_id, user_id)
        else:
            version = -1
        processed = self.autosave_tool.is_form_processed(form_id, user_id) 

        # The user wants to enter data in the form again, so we'll mark it as undone.
        self.autosave_tool.mark_form_unprocessed(form_id, user_id)
        return json.dumps({'version': version, 'processed': processed})

    def save_form(self):
        """ Saves all values of the submitted form.
        """
        form = self.request.form
        form_id = form.get('form_id', None)
        version = form.get('form_version', None)
        user_id = self.get_user_id()

        if form_id is None or user_id is None:
            return

        try:
            fields = self.autosave_tool.get_form_fields(form_id)
        except IndexError:
            # That was a bad ID.
            return

        data = {}
        for field_name, field_type in fields.items():
            data[field_name] = form.get(field_name, None)

        self.autosave_tool.save_form(form_id, user_id, version, data)

    @jquery
    def load_form(self):
        """ Updates the page with the stored data.
        """
        form = self.request.form
        form_id = form.get('form_id', None)
        user_id = self.get_user_id()

        if form_id is None or user_id is None:
            return

        try:
            data = self.autosave_tool.load_form(form_id, user_id)
            fields = self.autosave_tool.get_form_fields(form_id)
        except IndexError:
            return


        jq = JQueryProxy()

        for field_name, value in data.items():
            try:
                field_type = fields.get(field_name)
            except IndexError:
                # This field might have been deleted.
                continue

            if field_type == config.SELECT:
                if not isinstance(value, list):
                    value = [value]
                for val in value:
                    jq('#%s select[name=%s] option[value=%s]' % (form_id, field_name, val)).attr('selected', 'selected')
            elif field_type in [config.CHECKBOX, config.RADIO]:
                if not isinstance(value, list):
                    value = [value]
                for val in value:
                    if val == 'on':
                        jq('#%s input[name=%s]' % (form_id, field_name)).attr('checked', 'checked')
                    else:
                        jq('#%s input[name=%s][value=%s]' % (form_id, field_name, val)).attr('checked', 'checked')
            else:
                jq('#%s [name=%s]' % (form_id, field_name)).attr('value', value)

        return jq
        
class RegisterSampleForm(AutoSaveAjax):
    """ Simple view use to enable the form located at page 'autosave_sample'
    """
    def __call__(self):
        fields = {'text_field': config.TEXT,
                  'radio_field': config.RADIO,
                  'checkbox_field': config.CHECKBOX,
                  'checkbox_field_no_value': config.CHECKBOX,
                  'multi_checkbox_field': config.CHECKBOX,
                  'select_field': config.SELECT,
                  'multi_select_field': config.SELECT,
                  'textarea_field': config.TEXTAREA}
        try:
            self.autosave_tool.register_form('autosave_sample', fields)
            return 'Form registered'
        except IndexError:
            # The form is already registered.
            self.autosave_tool.update_form_fields('autosave_sample', fields)
            return 'The form is already registered - fields have been updated'


class ProcessSampleForm(AutoSaveAjax):
    """ 
    """
    def __call__(self):
        user_id = self.get_user_id()
        self.autosave_tool.mark_form_processed('autosave_sample', user_id)
        return self.request.RESPONSE.redirect('autosave_sample')
