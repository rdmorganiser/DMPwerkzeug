from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from rdmo.conditions.models import Condition
from rdmo.core.constants import VALUE_TYPE_CHOICES
from rdmo.core.models import Model, TranslationMixin
from rdmo.core.utils import copy_model, join_url
from rdmo.domain.models import Attribute
from rdmo.options.models import Option

from ..managers import QuestionManager
from .questionset import QuestionSet


class Question(Model, TranslationMixin):

    WIDGET_TYPE_CHOICES = (
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('yesno', 'Yes/No'),
        ('checkbox', 'Checkboxes'),
        ('radio', 'Radio buttons'),
        ('select', 'Select drop-down'),
        ('autocomplete', 'Autocomplete'),
        ('range', 'Range slider'),
        ('date', 'Date picker'),
        ('file', 'File upload')
    )

    objects = QuestionManager()

    uri = models.URLField(
        max_length=640, blank=True, null=True,
        verbose_name=_('URI'),
        help_text=_('The Uniform Resource Identifier of this question (auto-generated).')
    )
    uri_prefix = models.URLField(
        max_length=256,
        verbose_name=_('URI Prefix'),
        help_text=_('The prefix for the URI of this question.')
    )
    key = models.SlugField(
        max_length=128, blank=True, null=True,
        verbose_name=_('Key'),
        help_text=_('The internal identifier of this question.')
    )
    path = models.CharField(
        max_length=512, blank=True, null=True,
        verbose_name=_('Path'),
        help_text=_('The path part of the URI of this question (auto-generated).')
    )
    comment = models.TextField(
        blank=True, null=True,
        verbose_name=_('Comment'),
        help_text=_('Additional internal information about this question.')
    )
    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Designates whether this question can be changed.')
    )
    attribute = models.ForeignKey(
        Attribute, blank=True, null=True, on_delete=models.SET_NULL, related_name='questions',
        verbose_name=_('Attribute'),
        help_text=_('The attribute this question belongs to.')
    )
    questionset = models.ForeignKey(
        QuestionSet, on_delete=models.CASCADE, related_name='questions',
        verbose_name=_('Questionset'),
        help_text=_('The question set this question belongs to.')
    )
    is_collection = models.BooleanField(
        default=False,
        verbose_name=_('is collection'),
        help_text=_('Designates whether this question is a collection.')
    )
    is_optional = models.BooleanField(
        default=False,
        verbose_name=_('is optional'),
        help_text=_('Designates whether this question is optional.')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('The position of this question in lists.')
    )
    help_lang1 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Help (primary)'),
        help_text=_('The help text for this question in the primary language.')
    )
    help_lang2 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Help (secondary)'),
        help_text=_('The help text for this question in the secondary language.')
    )
    help_lang3 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Help (tertiary)'),
        help_text=_('The help text for this question in the tertiary language.')
    )
    help_lang4 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Help (quaternary)'),
        help_text=_('The help text for this question in the quaternary language.')
    )
    help_lang5 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Help (quinary)'),
        help_text=_('The help text for this question in the quinary language.')
    )
    text_lang1 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Text (primary)'),
        help_text=_('The text for this question in the primary language.')
    )
    text_lang2 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Text (secondary)'),
        help_text=_('The text for this question in the secondary language.')
    )
    text_lang3 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Text (tertiary)'),
        help_text=_('The text for this question in the tertiary language.')
    )
    text_lang4 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Text (quaternary)'),
        help_text=_('The text for this question in the quaternary language.')
    )
    text_lang5 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Text (quinary)'),
        help_text=_('The text for this question in the quinary language.')
    )
    default_text_lang1 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Default text value (primary)'),
        help_text=_('The default text value for this question in the primary language.')
    )
    default_text_lang2 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Default text value (secondary)'),
        help_text=_('The default text value for this question in the secondary language.')
    )
    default_text_lang3 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Default text value (tertiary)'),
        help_text=_('The default text value for this question in the tertiary language.')
    )
    default_text_lang4 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Default text value (quaternary)'),
        help_text=_('The default text value for this question in the quaternary language.')
    )
    default_text_lang5 = models.TextField(
        null=True, blank=True,
        verbose_name=_('Default text value (quinary)'),
        help_text=_('The default text value for this question in the quinary language.')
    )
    default_option = models.ForeignKey(
        Option, blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_('Default option'),
        help_text=_('The default option for this question. To be used with regular optionsets.')
    )
    default_external_id = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Default external id'),
        help_text=_('The default external id for this question. To be used with dynamic optionsets.')
    )
    verbose_name_lang1 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (primary)'),
        help_text=_('The name displayed for this question in the primary language.')
    )
    verbose_name_lang2 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (secondary)'),
        help_text=_('The name displayed for this question in the secondary language.')
    )
    verbose_name_lang3 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (tertiary)'),
        help_text=_('The name displayed for this question in the tertiary language.')
    )
    verbose_name_lang4 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (quaternary)'),
        help_text=_('The name displayed for this question in the quaternary language.')
    )
    verbose_name_lang5 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (quinary)'),
        help_text=_('The name displayed for this question in the quinary language.')
    )
    verbose_name_plural_lang1 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Plural name (primary)'),
        help_text=_('The plural name displayed for this question in the primary language.')
    )
    verbose_name_plural_lang2 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Plural name (secondary)'),
        help_text=_('The plural name displayed for this question in the secondary language.')
    )
    verbose_name_plural_lang3 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Plural name (tertiary)'),
        help_text=_('The plural name displayed for this question in the tertiary language.')
    )
    verbose_name_plural_lang4 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Plural name (quaternary)'),
        help_text=_('The plural name displayed for this question in the quaternary language.')
    )
    verbose_name_plural_lang5 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Plural name (quinary)'),
        help_text=_('The plural name displayed for this question in the quinary language.')
    )
    widget_type = models.CharField(
        max_length=12, choices=WIDGET_TYPE_CHOICES,
        verbose_name=_('Widget type'),
        help_text=_('Type of widget for this question.')
    )
    value_type = models.CharField(
        max_length=8, choices=VALUE_TYPE_CHOICES,
        verbose_name=_('Value type'),
        help_text=_('Type of value for this question.')
    )
    minimum = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Minimum'),
        help_text=_('Minimal value for this question.')
    )
    maximum = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Maximum'),
        help_text=_('Maximum value for this question.')
    )
    step = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Step'),
        help_text=_('Step in which the value for this question can be incremented/decremented.')
    )
    unit = models.CharField(
        max_length=64, blank=True,
        verbose_name=_('Unit'),
        help_text=_('Unit for this question.')
    )
    width = models.IntegerField(
        null=True, blank=True,
        verbose_name=_('Width'),
        help_text=_('Width for the widget of this question (optional, full with: 12).')
    )
    optionsets = models.ManyToManyField(
        'options.OptionSet', blank=True, related_name='questions',
        verbose_name=_('Option sets'),
        help_text=_('Option sets for this question.')
    )
    conditions = models.ManyToManyField(
        Condition, blank=True, related_name='questions',
        verbose_name=_('Conditions'),
        help_text=_('List of conditions evaluated for this question.')
    )

    class Meta:
        ordering = ('questionset', 'order')
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        self.path = self.build_path(self.key, self.questionset)
        self.uri = self.build_uri(self.uri_prefix, self.path)
        super().save(*args, **kwargs)

    def copy(self, uri_prefix, key, questionset=None):
        question = copy_model(self, uri_prefix=uri_prefix, key=key, questionset=questionset or self.questionset, attribute=self.attribute)

        # copy m2m fields
        question.optionsets.set(self.optionsets.all())
        question.conditions.set(self.conditions.all())

        return question

    @property
    def parent_fields(self):
        return ('questionset', )

    @property
    def text(self):
        return self.trans('text')

    @property
    def help(self):
        return self.trans('help')

    @property
    def default_text(self):
        return self.trans('default_text')

    @property
    def verbose_name(self):
        return self.trans('verbose_name')

    @property
    def verbose_name_plural(self):
        return self.trans('verbose_name_plural')

    @property
    def is_locked(self):
        return self.locked or self.questionset.is_locked

    @property
    def is_question(self):
        return True

    @property
    def has_conditions(self):
        return self.conditions.exists()

    @classmethod
    def build_path(cls, key, questionset):
        assert key
        assert questionset
        return questionset.path + '/' + key

    @classmethod
    def build_uri(cls, uri_prefix, path):
        assert path
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/questions/', path)
