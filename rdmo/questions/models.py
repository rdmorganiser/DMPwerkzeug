from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.cache import caches
from django.db import models
from django.utils.translation import ugettext_lazy as _

from rdmo.conditions.models import Condition
from rdmo.core.constants import VALUE_TYPE_CHOICES
from rdmo.core.models import Model, TranslationMixin
from rdmo.core.utils import copy_model, get_language_fields, join_url
from rdmo.domain.models import Attribute

from .managers import CatalogManager, QuestionManager, QuestionSetManager


class Catalog(Model, TranslationMixin):

    objects = CatalogManager()

    uri = models.URLField(
        max_length=640, blank=True,
        verbose_name=_('URI'),
        help_text=_('The Uniform Resource Identifier of this catalog (auto-generated).')
    )
    uri_prefix = models.URLField(
        max_length=256,
        verbose_name=_('URI Prefix'),
        help_text=_('The prefix for the URI of this catalog.')
    )
    key = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Key'),
        help_text=_('The internal identifier of this catalog.')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Comment'),
        help_text=_('Additional internal information about this catalog.')
    )
    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Designates whether this catalog (and it\'s sections, question sets and questions) can be changed.')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('The position of this catalog in lists.')
    )
    sites = models.ManyToManyField(
        Site, blank=True,
        verbose_name=_('Sites'),
        help_text=_('The sites this catalog belongs to (in a multi site setup).')
    )
    groups = models.ManyToManyField(
        Group, blank=True,
        verbose_name=_('Group'),
        help_text=_('The groups for which this catalog is active.')
    )
    title_lang1 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (primary)'),
        help_text=_('The title for this catalog in the primary language.')
    )
    title_lang2 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (secondary)'),
        help_text=_('The title for this catalog in the secondary language.')
    )
    title_lang3 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (tertiary)'),
        help_text=_('The title for this catalog in the tertiary language.')
    )
    title_lang4 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (quaternary)'),
        help_text=_('The title for this catalog in the quaternary language.')
    )
    title_lang5 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (quinary)'),
        help_text=_('The title for this catalog in the quinary language.')
    )
    help_lang1 = models.TextField(
        blank=True,
        verbose_name=_('Help (primary)'),
        help_text=_('The help text for this catalog in the primary language.')
    )
    help_lang2 = models.TextField(
        blank=True,
        verbose_name=_('Help (secondary)'),
        help_text=_('The help text for this catalog in the secondary language.')
    )
    help_lang3 = models.TextField(
        blank=True,
        verbose_name=_('Help (tertiary)'),
        help_text=_('The help text for this catalog in the tertiary language.')
    )
    help_lang4 = models.TextField(
        blank=True,
        verbose_name=_('Help (quaternary)'),
        help_text=_('The help text for this catalog in the quaternary language.')
    )
    help_lang5 = models.TextField(
        blank=True,
        verbose_name=_('Help (quinary)'),
        help_text=_('The help text for this catalog in the quinary language.')
    )
    available = models.BooleanField(
        default=True,
        verbose_name=_('Available'),
        help_text=_('Designates whether this catalog is generally available for projects.')
    )

    class Meta:
        ordering = ('order',)
        verbose_name = _('Catalog')
        verbose_name_plural = _('Catalogs')

    def __str__(self):
        return self.key

    def save(self, *args, **kwargs):
        self.uri = self.build_uri(self.uri_prefix, self.key)
        super().save(*args, **kwargs)

        for section in self.sections.all():
            section.save()

    def copy(self, uri_prefix, key):
        # create a new title
        kwargs = {}
        for field in get_language_fields('title'):
            kwargs[field] = getattr(self, field) + '*'

        # copy instance
        catalog = copy_model(self, uri_prefix=uri_prefix, key=key, **kwargs)

        # copy m2m fields
        catalog.sites.set(self.sites.all())
        catalog.groups.set(self.groups.all())

        # copy children
        for section in self.sections.all():
            section.copy(uri_prefix, section.key, catalog=catalog)

        return catalog

    @property
    def title(self):
        return self.trans('title')

    @property
    def help(self):
        return self.trans('help')

    @property
    def is_locked(self):
        return self.locked

    @classmethod
    def build_uri(cls, uri_prefix, key):
        assert key
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/questions/', key)


class Section(Model, TranslationMixin):

    uri = models.URLField(
        max_length=640, blank=True,
        verbose_name=_('URI'),
        help_text=_('The Uniform Resource Identifier of this section (auto-generated).')
    )
    uri_prefix = models.URLField(
        max_length=256,
        verbose_name=_('URI Prefix'),
        help_text=_('The prefix for the URI of this section.')
    )
    key = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Key'),
        help_text=_('The internal identifier of this section.')
    )
    path = models.CharField(
        max_length=512, blank=True,
        verbose_name=_('Label'),
        help_text=_('The path part of the URI of this section (auto-generated).')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Comment'),
        help_text=_('Additional internal information about this section.')
    )
    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Designates whether this section (and it\'s question sets and questions) can be changed.')
    )
    catalog = models.ForeignKey(
        Catalog, on_delete=models.CASCADE, related_name='sections',
        verbose_name=_('Catalog'),
        help_text=_('The catalog this section belongs to.')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('Position in lists.')
    )
    title_lang1 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (primary)'),
        help_text=_('The title for this section in the primary language.')
    )
    title_lang2 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (secondary)'),
        help_text=_('The title for this section in the secondary language.')
    )
    title_lang3 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (tertiary)'),
        help_text=_('The title for this section in the tertiary language.')
    )
    title_lang4 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (quaternary)'),
        help_text=_('The title for this section in the quaternary language.')
    )
    title_lang5 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (quinary)'),
        help_text=_('The title for this section in the quinary language.')
    )

    class Meta:
        ordering = ('catalog__order', 'order')
        verbose_name = _('Section')
        verbose_name_plural = _('Sections')

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        self.path = self.build_path(self.key, self.catalog)
        self.uri = self.build_uri(self.uri_prefix, self.path)

        super().save(*args, **kwargs)

        for questionsets in self.questionsets.all():
            questionsets.save()

    def copy(self, uri_prefix, key, catalog=None):
        section = copy_model(self, uri_prefix=uri_prefix, key=key, catalog=catalog or self.catalog)

        # copy children
        for questionset in self.questionsets.all():
            questionset.copy(uri_prefix, questionset.key, section=section)

        return section

    @property
    def parent(self):
        return self.catalog

    @property
    def parent_field(self):
        return 'catalog'

    @property
    def title(self):
        return self.trans('title')

    @property
    def is_locked(self):
        return self.locked or self.catalog.is_locked

    @classmethod
    def build_path(cls, key, catalog):
        assert key
        assert catalog
        return '%s/%s' % (catalog.key, key)

    @classmethod
    def build_uri(cls, uri_prefix, path):
        assert path
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/questions/', path)


class QuestionSet(Model, TranslationMixin):

    objects = QuestionSetManager()

    uri = models.URLField(
        max_length=640, blank=True,
        verbose_name=_('URI'),
        help_text=_('The Uniform Resource Identifier of this questionset (auto-generated).')
    )
    uri_prefix = models.URLField(
        max_length=256,
        verbose_name=_('URI Prefix'),
        help_text=_('The prefix for the URI of this questionset.')
    )
    key = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Key'),
        help_text=_('The internal identifier of this questionset.')
    )
    path = models.CharField(
        max_length=512, blank=True,
        verbose_name=_('Path'),
        help_text=_('The path part of the URI of this questionset (auto-generated).')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Comment'),
        help_text=_('Additional internal information about this questionset.')
    )
    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Designates whether this questionset (and it\'s questions) can be changed.')
    )
    attribute = models.ForeignKey(
        Attribute, blank=True, null=True, related_name='questionsets',
        on_delete=models.SET_NULL,
        verbose_name=_('Attribute'),
        help_text=_('The attribute this questionset belongs to.')
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name='questionsets',
        verbose_name=_('Section'),
        help_text=_('The section this questionset belongs to.')
    )
    is_collection = models.BooleanField(
        default=False,
        verbose_name=_('is collection'),
        help_text=_('Designates whether this questionset is a collection.')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('The position of this questionset in lists.')
    )
    title_lang1 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (primary)'),
        help_text=_('The title for this questionset in the primary language.')
    )
    title_lang2 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (secondary)'),
        help_text=_('The title for this questionset in the secondary language.')
    )
    title_lang3 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (tertiary)'),
        help_text=_('The title for this questionset in the tertiary language.')
    )
    title_lang4 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (quaternary)'),
        help_text=_('The title for this questionset in the quaternary language.')
    )
    title_lang5 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Title (quinary)'),
        help_text=_('The title for this questionset in the quinary language.')
    )
    help_lang1 = models.TextField(
        blank=True,
        verbose_name=_('Help (primary)'),
        help_text=_('The help text for this questionset in the primary language.')
    )
    help_lang2 = models.TextField(
        blank=True,
        verbose_name=_('Help (secondary)'),
        help_text=_('The help text for this questionset in the secondary language.')
    )
    help_lang3 = models.TextField(
        blank=True,
        verbose_name=_('Help (tertiary)'),
        help_text=_('The help text for this questionset in the tertiary language.')
    )
    help_lang4 = models.TextField(
        blank=True,
        verbose_name=_('Help (quaternary)'),
        help_text=_('The help text for this questionset in the quaternary language.')
    )
    help_lang5 = models.TextField(
        blank=True,
        verbose_name=_('Help (quinary)'),
        help_text=_('The help text for this questionset in the quinary language.')
    )
    verbose_name_lang1 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (primary)'),
        help_text=_('The name displayed for this question in the primary language.')
    )
    verbose_name_lang2 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (secondary)'),
        help_text=_('The  name displayed for this question in the secondary language.')
    )
    verbose_name_lang3 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (tertiary)'),
        help_text=_('The  name displayed for this question in the tertiary language.')
    )
    verbose_name_lang4 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (quaternary)'),
        help_text=_('The  name displayed for this question in the quaternary language.')
    )
    verbose_name_lang5 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Name (quinary)'),
        help_text=_('The  name displayed for this question in the quinary language.')
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
    conditions = models.ManyToManyField(
        Condition, blank=True, related_name='questionsets',
        verbose_name=_('Conditions'),
        help_text=_('List of conditions evaluated for this questionset.')
    )

    class Meta:
        ordering = ('section', 'order')
        verbose_name = _('Question set')
        verbose_name_plural = _('Question set')

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        self.path = self.build_path(self.key, self.section)
        self.uri = self.build_uri(self.uri_prefix, self.path)

        super().save(*args, **kwargs)

        for question in self.questions.all():
            question.save()

        # invalidate the cache so that changes appear instantly
        caches['api'].clear()

    def copy(self, uri_prefix, key, section=None):
        questionset = copy_model(self, uri_prefix=uri_prefix, key=key, section=section or self.section, attribute=self.attribute)

        # copy m2m fields
        questionset.conditions.set(self.conditions.all())

        # copy children
        for question in self.questions.all():
            question.copy(uri_prefix, question.key, questionset=questionset)

        return questionset

    @property
    def parent(self):
        return self.section

    @property
    def parent_field(self):
        return 'section'

    @property
    def title(self):
        return self.trans('title')

    @property
    def help(self):
        return self.trans('help')

    @property
    def verbose_name(self):
        return self.trans('verbose_name')

    @property
    def verbose_name_plural(self):
        return self.trans('verbose_name_plural')

    @property
    def is_locked(self):
        return self.locked or self.section.is_locked

    @classmethod
    def build_path(cls, key, section):
        assert key
        assert section
        return '%s/%s/%s' % (
            section.catalog.key,
            section.key,
            key
        )

    @classmethod
    def build_uri(cls, uri_prefix, path):
        assert path
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/questions/', path)


class Question(Model, TranslationMixin):

    WIDGET_TYPE_CHOICES = (
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('yesno', 'Yes/No'),
        ('checkbox', 'Checkboxes'),
        ('radio', 'Radio buttons'),
        ('select', 'Select drop-down'),
        ('range', 'Range slider'),
        ('date', 'Date picker'),
        ('file', 'File upload'),
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

        # invalidate the cache so that changes appear instantly
        caches['api'].clear()

    def copy(self, uri_prefix, key, questionset=None):
        question = copy_model(self, uri_prefix=uri_prefix, key=key, questionset=questionset or self.questionset, attribute=self.attribute)

        # copy m2m fields
        question.optionsets.set(self.optionsets.all())
        question.conditions.set(self.conditions.all())

        return question

    @property
    def parent(self):
        return self.questionset

    @property
    def parent_field(self):
        return 'questionset'

    @property
    def text(self):
        return self.trans('text')

    @property
    def help(self):
        return self.trans('help')

    @property
    def verbose_name(self):
        return self.trans('verbose_name')

    @property
    def verbose_name_plural(self):
        return self.trans('verbose_name_plural')

    @property
    def is_locked(self):
        return self.locked or self.questionset.is_locked

    @classmethod
    def build_path(cls, key, questionset):
        assert key
        assert questionset
        return '%s/%s/%s/%s' % (
            questionset.section.catalog.key,
            questionset.section.key,
            questionset.key,
            key
        )

    @classmethod
    def build_uri(cls, uri_prefix, path):
        assert path
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/questions/', path)
