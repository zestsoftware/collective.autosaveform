from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from jquery.pyproxy.plone import jquery, JQueryProxy

import config

class AutoSaveAjax(BrowserView):
    @property
    def autosave_tool(self):
        return getToolByName(self.context, 'portal_autosaveform')

    @property
    def mtool(self):
        return getToolByName(aq_inner(self.context),
                             'portal_membership')

    def get_user_id(self):
        if self.mtool.isAnonymousUser():
            return
        user = self.mtool.getAuthenticatedMember()
        return user.id

    def save_form(self):
        form = self.request.form
        form_id = form.get('form_id', None)
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

        self.autosave_tool.save_form(form_id, user_id, data)

    @jquery
    def load_form(self):
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
                    jq('#%s input[name=%s][value=%s]' % (form_id, field_name, val)).attr('checked', 'checked')
            else:
                jq('#%s [name=%s]' % (form_id, field_name)).attr('value', value)

        return jq
        
class RegisterSampleForm(BrowserView):
    def __call__(self):
        tool = getToolByName(self.context, 'portal_autosaveform')
        try:
            tool.register_form(
                'autosave_sample',
                {'text_field': config.TEXT,
                 'radio_field': config.RADIO,
                 'checkbox_field': config.CHECKBOX,
                 'multi_checkbox_field': config.CHECKBOX,
                 'select_field': config.SELECT,
                 'multi_select_field': config.SELECT,
                 'textarea_field': config.TEXTAREA})
            return 'Form registered'
        except IndexError:
            # The form is already registered.
            return 'The form is already registered'
