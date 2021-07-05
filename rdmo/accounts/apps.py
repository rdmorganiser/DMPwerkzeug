from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    name = 'rdmo.accounts'
    verbose_name = _('Accounts')

    def ready(self):
        from . import rules
