from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from rdmo.core.constants import VALUE_TYPE_FILE
from rdmo.core.utils import human2bytes


class ValueValidator(object):

    requires_context = True

    def __call__(self, data, serializer):
        if data.get('value_type') == VALUE_TYPE_FILE:
            try:
                serializer.context['view'].get_object()
            except AssertionError:
                project = serializer.context['view'].project

                if project.file_size > human2bytes(settings.PROJECT_FILE_QUOTA):
                    raise serializers.ValidationError({
                        'value': [_('You reached the file quota for this project.')]
                    })
