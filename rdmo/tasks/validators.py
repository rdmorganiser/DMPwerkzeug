from django.utils.translation import gettext_lazy as _

from rdmo.core.validators import LockedValidator, UniqueURIValidator

from .models import Task


class TaskUniqueURIValidator(UniqueURIValidator):

    model = Task

    def get_uri(self, data):
        if not data.get('key'):
            self.raise_validation_error({'key': _('This field is required.')})
        else:
            uri = self.model.build_uri(data.get('uri_prefix'), data.get('key'))
            return uri


class TaskLockedValidator(LockedValidator):

    pass
