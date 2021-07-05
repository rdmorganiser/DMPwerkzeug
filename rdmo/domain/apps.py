from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DomainConfig(AppConfig):
    name = 'rdmo.domain'
    verbose_name = _('Domain')
