from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ManagementConfig(AppConfig):
    name = 'rdmo.management'
    verbose_name = _('Management')
