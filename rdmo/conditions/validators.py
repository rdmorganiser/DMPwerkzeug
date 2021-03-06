from django.utils.translation import ugettext_lazy as _

from rdmo.core.validators import LockedValidator, UniqueURIValidator

from .models import Condition


class ConditionUniqueURIValidator(UniqueURIValidator):

    model = Condition

    def get_uri(self, data):
        if data.get('key') is None:
            self.raise_validation_error({'key': _('This field is required.')})
        else:
            uri = self.model.build_uri(data.get('uri_prefix'), data.get('key'))
            return uri


class ConditionLockedValidator(LockedValidator):

    pass
