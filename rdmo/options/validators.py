from django.utils.translation import gettext_lazy as _

from rdmo.core.validators import LockedValidator, UniqueURIValidator

from .models import Option, OptionSet


class OptionSetUniqueURIValidator(UniqueURIValidator):

    model = OptionSet

    def get_uri(self, data):
        if not data.get('key'):
            self.raise_validation_error({'key': _('This field is required.')})
        else:
            uri = self.model.build_uri(data.get('uri_prefix'), data.get('key'))
            return uri


class OptionUniqueURIValidator(UniqueURIValidator):

    model = Option

    def get_uri(self, data):
        if not data.get('key'):
            self.raise_validation_error({'key': _('This field is required.')})
        elif not data.get('optionset'):
            self.raise_validation_error({'optionset': _('This field may not be null.')})
        else:
            path = self.model.build_path(data.get('key'), data.get('optionset'))
            uri = self.model.build_uri(data.get('uri_prefix'), path)
            return uri


class OptionSetLockedValidator(LockedValidator):

    pass


class OptionLockedValidator(LockedValidator):

    parent_field = 'optionset'
