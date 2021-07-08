from datetime import date, timedelta
from itertools import zip_longest

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from rdmo.tasks.models import Task

from ..managers import IssueManager


class Issue(models.Model):

    objects = IssueManager()

    ISSUE_STATUS_OPEN = 'open'
    ISSUE_STATUS_IN_PROGRESS = 'in_progress'
    ISSUE_STATUS_CLOSED = 'closed'
    ISSUE_STATUS_CHOICES = (
        (ISSUE_STATUS_OPEN, _('open')),
        (ISSUE_STATUS_IN_PROGRESS, _('in progress')),
        (ISSUE_STATUS_CLOSED, _('closed'))
    )

    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, related_name='issues',
        verbose_name=_('Project'),
        help_text=_('The project for this issue.')
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='issues',
        verbose_name=_('Task'),
        help_text=_('The task for this issue.')
    )
    status = models.CharField(
        max_length=12, choices=ISSUE_STATUS_CHOICES, default=ISSUE_STATUS_OPEN,
        verbose_name=_('Status'),
        help_text=_('The status for this issue.')
    )

    class Meta:
        ordering = ('project__title', )
        verbose_name = _('Issue')
        verbose_name_plural = _('Issues')

    def __str__(self):
        return '%s / %s / %s' % (self.project.title, self.task, self.status)

    def get_absolute_url(self):
        return reverse('project', kwargs={'pk': self.project.pk})

    def resolve(self):
        values = self.project.values.filter(snapshot=None)
        for condition in self.task.conditions.all():
            if condition.resolve(values):
                return True

    @property
    def dates(self):
        values = self.project.values.filter(snapshot=None)

        if self.task.start_attribute:
            start_values = values.filter(attribute=self.task.start_attribute)
        else:
            start_values = []

        if self.task.end_attribute:
            end_values = values.filter(attribute=self.task.end_attribute)
        else:
            end_values = []

        days_before = timedelta(self.task.days_before) if self.task.days_before else timedelta()
        days_after = timedelta(self.task.days_after) if self.task.days_after else timedelta()

        dates = []
        for start_value, end_value in zip_longest(start_values, end_values):

            if start_value and start_value.value and isinstance(start_value.value, date):
                start_date = start_value.value
            else:
                start_date = None

            if end_value and end_value.value and isinstance(end_value.value, date):
                end_date = end_value.value
            else:
                end_date = None

            if start_date and end_date:
                dates.append((start_date - days_before, end_date + days_after))
            elif start_date:
                dates.append((start_date - days_before + days_after, ))
            elif end_date:
                dates.append((end_date - days_before + days_after, ))

        return dates


class IssueResource(models.Model):

    issue = models.ForeignKey(
        'Issue', on_delete=models.CASCADE, related_name='resources',
        verbose_name=_('Issue'),
        help_text=_('The issue for this issue resource.')
    )
    integration = models.ForeignKey(
        'Integration', on_delete=models.CASCADE, related_name='resources',
        verbose_name=_('Integration'),
        help_text=_('The integration for this issue resource.')
    )
    url = models.URLField(
        verbose_name=_('URL'),
        help_text=_('The URL of this issue resource.')
    )

    class Meta:
        ordering = ('issue__project__title', 'issue')
        verbose_name = _('Issue resource')
        verbose_name_plural = _('Issue resources')

    def __str__(self):
        return '%s / %s / %s' % (self.issue.project.title, self.issue, self.url)
