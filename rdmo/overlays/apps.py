from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OverlayConfig(AppConfig):
    name = 'rdmo.overlays'
    verbose_name = _('Overlays')
