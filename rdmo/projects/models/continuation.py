from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from rdmo.core.models import Model
from rdmo.questions.models import QuestionSet


class Continuation(Model):

    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, related_name='+',
        verbose_name=_('Project'),
        help_text=_('The project for this continuation.')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+',
        verbose_name=_('User'),
        help_text=_('The user for this continuation.')
    )
    questionset = models.ForeignKey(
        QuestionSet, on_delete=models.CASCADE, related_name='+',
        verbose_name=_('Question set'),
        help_text=_('The question set for this continuation.')
    )

    class Meta:
        ordering = ('user', 'project')
        verbose_name = _('Continuation')
        verbose_name_plural = _('Continuations')

    def __str__(self):
        return '%s/%s/%s' % (self.project, self.user, self.questionset)
