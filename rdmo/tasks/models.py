from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy as _
from rdmo.conditions.models import Condition
from rdmo.core.models import TranslationMixin
from rdmo.core.utils import copy_model, join_url
from rdmo.domain.models import Attribute
from rdmo.questions.models import Catalog

from .managers import TaskManager


class Task(TranslationMixin, models.Model):

    objects = TaskManager()

    uri = models.URLField(
        max_length=640, blank=True,
        verbose_name=_('URI'),
        help_text=_('The Uniform Resource Identifier of this task (auto-generated).')
    )
    uri_prefix = models.URLField(
        max_length=256,
        verbose_name=_('URI Prefix'),
        help_text=_('The prefix for the URI of this task.')
    )
    key = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Key'),
        help_text=_('The internal identifier of this task.')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Comment'),
        help_text=_('Additional internal information about this task.')
    )
    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Designates whether this task can be changed.')
    )
    catalogs = models.ManyToManyField(
        Catalog, blank=True,
        verbose_name=_('Catalogs'),
        help_text=_('The catalogs this task can be used with. An empty list implies that this task can be used with every catalog.')
    )
    sites = models.ManyToManyField(
        Site, blank=True,
        verbose_name=_('Sites'),
        help_text=_('The sites this task belongs to (in a multi site setup).')
    )
    groups = models.ManyToManyField(
        Group, blank=True,
        verbose_name=_('Group'),
        help_text=_('The groups for which this task is active.')
    )
    title_lang1 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (primary)'),
        help_text=_('The title for this task in the primary language.')
    )
    title_lang2 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (secondary)'),
        help_text=_('The title for this task in the secondary language.')
    )
    title_lang3 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (tertiary)'),
        help_text=_('The title for this task in the tertiary language.')
    )
    title_lang4 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (quaternary)'),
        help_text=_('The title for this task in the quaternary language.')
    )
    title_lang5 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (quinary)'),
        help_text=_('The title for this task in the quinary language.')
    )
    text_lang1 = models.TextField(
        blank=True,
        verbose_name=_('Text (primary)'),
        help_text=_('The text for this task in the primary language.')
    )
    text_lang2 = models.TextField(
        blank=True,
        verbose_name=_('Text (secondary)'),
        help_text=_('The text for this task in the secondary language.')
    )
    text_lang3 = models.TextField(
        blank=True,
        verbose_name=_('Text (tertiary)'),
        help_text=_('The text for this task in the tertiary language.')
    )
    text_lang4 = models.TextField(
        blank=True,
        verbose_name=_('Text (quaternary)'),
        help_text=_('The text for this task in the quaternary language.')
    )
    text_lang5 = models.TextField(
        blank=True,
        verbose_name=_('Text (quinary)'),
        help_text=_('The text for this task in the quinary language.')
    )
    start_attribute = models.ForeignKey(
        Attribute, blank=True, null=True, on_delete=models.SET_NULL, related_name='tasks_as_start',
        verbose_name=_('Start date attribute'),
        help_text=_('The attribute that is setting the start date for this task.')
    )
    end_attribute = models.ForeignKey(
        Attribute, blank=True, null=True, on_delete=models.SET_NULL, related_name='tasks_as_end',
        verbose_name=_('End date attribute'),
        help_text=_('The attribute that is setting the end date for this task (optional, if no end date attribute is given, the start date attribute sets also the end date).')
    )
    days_before = models.IntegerField(
        blank=True, null=True,
        verbose_name=_('Days before'),
        help_text=_('Additional days before the start date.')
    )
    days_after = models.IntegerField(
        blank=True, null=True,
        verbose_name=_('Days after'),
        help_text=_('Additional days after the end date.')
    )
    conditions = models.ManyToManyField(
        Condition, blank=True, related_name='tasks',
        verbose_name=_('Conditions'),
        help_text=_('The list of conditions evaluated for this task.')
    )
    available = models.BooleanField(
        default=True,
        verbose_name=_('Available'),
        help_text=_('Designates whether this task is generally available for projects.')
    )

    class Meta:
        ordering = ('uri',)
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

    def __str__(self):
        return self.key

    def save(self, *args, **kwargs):
        self.uri = self.build_uri(self.uri_prefix, self.key)
        super().save(*args, **kwargs)

    def copy(self, uri_prefix, key):
        task = copy_model(self, uri_prefix=uri_prefix, key=key, start_attribute=self.start_attribute, end_attribute=self.end_attribute)

        # add m2m fields
        task.catalogs.set(self.catalogs.all())
        task.sites.set(self.sites.all())
        task.groups.set(self.groups.all())
        task.conditions.set(self.conditions.all())

        return task

    @property
    def title(self):
        return self.trans('title')

    @property
    def text(self):
        return self.trans('text')

    @property
    def has_conditions(self):
        return bool(self.conditions.all())

    @property
    def is_locked(self):
        return self.locked

    @classmethod
    def build_uri(cls, uri_prefix, key):
        assert key
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/tasks/', key)
