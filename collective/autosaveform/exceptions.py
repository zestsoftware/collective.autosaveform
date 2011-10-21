class FormIdInUse(Exception):
    """ Exception raised when trying to register
    a form with an existing id.
    """

class UnregisteredForm(Exception):
    """ Exception raised when trying to access
    data for a frm that is not registered.
    """
