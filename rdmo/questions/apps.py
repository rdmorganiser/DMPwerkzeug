from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QuestionsConfig(AppConfig):
    name = 'rdmo.questions'
    verbose_name = _('Questions')
