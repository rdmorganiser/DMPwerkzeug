from django.utils.translation import gettext_lazy as _

from rdmo.core.validators import (InstanceValidator, LockedValidator,
                                  UniqueURIValidator)

from .models import Attribute


class AttributeUniqueURIValidator(UniqueURIValidator):

    model = Attribute

    def get_uri(self, data):
        if not data.get('key'):
            self.raise_validation_error({'key': _('This field is required.')})
        else:
            path = self.model.build_path(data.get('key'), data.get('parent'))
            uri = self.model.build_uri(data.get('uri_prefix'), path)
            return uri


class AttributeParentValidator(InstanceValidator):

    def __call__(self, data):
        parent = data.get('parent')
        if parent:
            if self.serializer:
                # check copied attributes
                view = self.serializer.context.get('view')
                if view and view.action == 'copy':
                    # get the original from the view when cloning an attribute
                    if parent in view.get_object().get_descendants(include_self=True):
                        self.raise_validation_error({
                            'parent': [_('An attribute may not be cloned to be a child of itself or one of its descendants.')]
                        })

            # only check updated attributes
            if self.instance:
                if parent in self.instance.get_descendants(include_self=True):
                    self.raise_validation_error({
                        'parent': [_('An attribute may not be moved to be a child of itself or one of its descendants.')]
                    })


class AttributeLockedValidator(LockedValidator):

    parent_field = 'parent'
