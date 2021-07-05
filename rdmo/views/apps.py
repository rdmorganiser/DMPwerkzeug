from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ViewsConfig(AppConfig):
    name = 'rdmo.views'
    verbose_name = _('Views')
