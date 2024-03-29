import os
import logging
from datetime import datetime

from AccessControl import Unauthorized
from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner, aq_parent
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from zope.annotation.interfaces import IAnnotations
from zope.interface import implements
from Products.Archetypes import atapi
from Products.CMFCore.utils import ImmutableId
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ModifyPortalContent
from Products.ATContentTypes.content.document import ATDocument
from Products.ATContentTypes.content.document import ATDocumentSchema
from zope.interface import Interface, implements

from collective.autosaveform import config, exceptions
from collective.autosaveform.utils import deep_seek

logger = logging.getLogger('collective.autosaveform.tool')

class IAutoSaveFormTool(Interface):
    """ marker interface"""

AutoSaveToolSchema = ATDocumentSchema.copy()

class AutoSaveFormTool(ImmutableId, ATDocument):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = ()
    implements(IAutoSaveFormTool)
    
    id = 'portal_autosaveform'
    typeDescription = ""
    typeDescMsgId = 'description_autosaveformtool'
    schema = AutoSaveToolSchema

    def __init__(self, *args, **kwargs):
        self.setTitle('Tool to register auto saved forms')

    security.declareProtected(ModifyPortalContent, 'indexObject')
    def indexObject(self):
        pass

    security.declareProtected(ModifyPortalContent, 'reindexObject')
    def reindexObject(self, idxs=[]):
        pass

    security.declareProtected(ModifyPortalContent, 'reindexObjectSecurity')
    def reindexObjectSecurity(self, skip_self=False):
        pass

    def _get_annotations(self):
        return IAnnotations(self)

    def _get_anno_by_key(self, key, value_type):
        anno = self._get_annotations()
        if not key in anno.keys():
            anno[key] = value_type()

        return anno[key]

    def _get_forms_list(self):
        return self._get_anno_by_key('autosave_form_ids',
                                     PersistentDict)

    def _get_saved_values(self):
        return self._get_anno_by_key('autosave_form_values',
                                     PersistentDict)

    def _get_saved_versions(self):
        return self._get_anno_by_key('autosave_form_versions',
                                     PersistentDict)

    def _get_processed_forms(self):
        return self._get_anno_by_key('autosave_form_processed',
                                     PersistentDict)

    def register_form(self, form_id, fields):
        """ Create a new entry in the list of forms.
        Raises a FormIdInUse exception if the id is already in use.
        """
        forms = self._get_forms_list()
        if form_id in forms.keys():
            raise exceptions.FormIdInUse(
                'A form is already registered with id "%s"' % form_id)

        forms[form_id] = PersistentDict()
        self.update_form_fields(form_id, fields)

    def get_form_fields(self, form_id):
        """ Returns the list of registered field for the form.
        """
        forms = self._get_forms_list()
        if not form_id in forms:
            raise exceptions.UnregisteredForm(
                'Unknown id "%s": this form has not been registered' % form_id)

        return dict([(k, v) for k, v in forms[form_id]['fields'].items()])

    def update_form_fields(self, form_id, fields):
        """ Updates the list of fields for a form.
        """
        forms = self._get_forms_list()
        if not form_id in forms:
            raise exceptions.UnregisteredForm(
                'Unknown id "%s": this form has not been registered' % form_id)

        # Erase previous entries.
        forms[form_id]['fields'] = PersistentDict()

        # Add the new ones.
        for field_id, field_type in fields.items():
            if not field_type in config.INPUT_TYPES:
                logging.info(
                    'Wrong field type for %s in form %s. Type %s unknown' % (field_id,
                                                                             form_id,
                                                                             field_type))
            forms[form_id]['fields'][field_id] = field_type

    def save_form(self, form_id, user_id, version, data):
        """ Registers, for the user, the values entered in
        the form.
        """
        forms = self._get_forms_list()
        values = self._get_saved_values()
        versions = self._get_saved_versions()

        if not form_id in forms:
            raise exceptions.UnregisteredForm(
                'Unknown id "%s": this form has not been registered' % form_id)

        if not form_id in values:
            values[form_id] = PersistentDict()

        values[form_id][user_id] = PersistentDict()
        for key, value in data.items():
            values[form_id][user_id][key] = value

        if not form_id in versions:
            versions[form_id] = PersistentDict()

        versions[form_id][user_id] = version

    def get_saved_version(self, form_id, user_id):
        """ Returns the saved version of the form.
        """
        versions = self._get_saved_versions()
        return deep_seek(versions, [form_id, user_id], -1)

    def is_form_processed(self, form_id, user_id):
        processed = self._get_processed_forms()
        return deep_seek(processed, [form_id, user_id], False)

    def load_form(self, form_id, user_id):
        """ Fetches the values the user entered for a given form.
        """
        values = self._get_saved_values()
        return dict(deep_seek(values, [form_id, user_id], {}).items())

    def mark_form_processed(self, form_id, user_id):
        """ Cleans values entered by the user once the form has
        been processed.
        """
        values = self._get_saved_values()
        versions = self._get_saved_versions()

        processed = self._get_processed_forms()
        if not form_id in processed:
            processed[form_id] = PersistentDict()
        processed[form_id][user_id] = True

        try:
            del values[form_id][user_id]
        except:
            logger.info('Can not delete values stored for user %s and form %s' % (user_id,
                                                                                  form_id))
            logger.info('values[%s]: %s | values[%s][%s]: %s' % (
                form_id,
                values.get(form_id, None),
                form_id,
                user_id,
                values.get(form_id, {}).get(user_id, None)))
                
        try:
            del versions[form_id][user_id]
        except:
            logger.info('Can not delete version stored for user %s and form %s' % (user_id,
                                                                                   form_id))
            logger.info('versions[%s]: %s | versions[%s][%s]: %s' % (
                form_id,
                versions.get(form_id, None),
                form_id,
                user_id,
                versions.get(form_id, {}).get(user_id, None)))


    def mark_form_unprocessed(self, form_id, user_id):
        processed = self._get_processed_forms()
        if not form_id in processed:
            processed[form_id] = PersistentDict()

        processed[form_id][user_id] = False

atapi.registerType(AutoSaveFormTool, config.PROJECTNAME)
