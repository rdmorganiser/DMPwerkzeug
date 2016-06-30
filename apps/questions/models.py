from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from apps.core.models import Model, TranslationMixin
from apps.domain.models import Attribute, AttributeSet

from .managers import QuestionEntityManager


@python_2_unicode_compatible
class Catalog(Model, TranslationMixin):

    title_en = models.CharField(max_length=256)
    title_de = models.CharField(max_length=256)

    class Meta:
        verbose_name = _('Catalog')
        verbose_name_plural = _('Catalogs')

    def __str__(self):
        return self.title

    @property
    def title(self):
        return self.trans('title')

    def get_absolute_url(self):
        return reverse('catalog', kwargs={'pk': self.pk})


@python_2_unicode_compatible
class Section(Model, TranslationMixin):

    catalog = models.ForeignKey(Catalog, related_name='sections')
    order = models.IntegerField(null=True)

    title_en = models.CharField(max_length=256)
    title_de = models.CharField(max_length=256)

    class Meta:
        ordering = ('order',)
        verbose_name = _('Section')
        verbose_name_plural = _('Sections')

    def __str__(self):
        return '%s / %s' % (self.catalog_title, self.title)

    def get_absolute_url(self):
        return reverse('catalog', kwargs={'pk': self.catalog.pk})

    @property
    def title(self):
        return self.trans('title')

    @property
    def catalog_title(self):
        return self.catalog.title


@python_2_unicode_compatible
class Subsection(Model, TranslationMixin):

    section = models.ForeignKey(Section, related_name='subsections')
    order = models.IntegerField(null=True)

    title_en = models.CharField(max_length=256)
    title_de = models.CharField(max_length=256)

    class Meta:
        ordering = ('order',)
        verbose_name = _('Subsection')
        verbose_name_plural = _('Subsections')

    def __str__(self):
        return '%s / %s / %s' % (self.catalog_title, self.section_title, self.title)

    def get_absolute_url(self):
        return reverse('catalog', kwargs={'pk': self.section.catalog.pk})

    @property
    def title(self):
        return self.trans('title')

    @property
    def catalog_title(self):
        return self.section.catalog.title

    @property
    def section_title(self):
        return self.section.title


class QuestionEntity(Model, TranslationMixin):

    objects = QuestionEntityManager()

    subsection = models.ForeignKey('Subsection', related_name='entities')
    order = models.IntegerField(null=True)

    title_en = models.CharField(max_length=256, null=True, blank=True)
    title_de = models.CharField(max_length=256, null=True, blank=True)

    help_en = models.TextField(null=True, blank=True)
    help_de = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ('order', )
        verbose_name = _('QuestionEntity')
        verbose_name_plural = _('QuestionEntities')

    def __str__(self):
        if self.is_set:
            return self.questionset.__str__()
        else:
            return self.question.__str__()

    def get_absolute_url(self):
        return reverse('catalog', kwargs={'pk': self.subsection.section.catalog.pk})

    @property
    def title(self):
        return self.trans('title')

    @property
    def help(self):
        return self.trans('help')

    @property
    def catalog_title(self):
        return self.subsection.section.catalog.title

    @property
    def section_title(self):
        return self.subsection.section.title

    @property
    def subsection_title(self):
        return self.subsection.title

    @property
    def is_set(self):
        return hasattr(self, 'questionset')

    @property
    def has_set(self):
        return hasattr(self, 'question') and hasattr(self.question, 'questionset') and self.question.questionset

    @property
    def tag(self):
        if self.is_set:
            return self.questionset.tag
        else:
            return self.question.tag

    @property
    def is_collection(self):
        if self.is_set:
            return self.questionset.is_collection
        else:
            return self.question.is_collection


@python_2_unicode_compatible
class QuestionSet(QuestionEntity):

    attributeset = models.ForeignKey(AttributeSet, blank=True, null=True, on_delete=models.SET_NULL, related_name='questionsets')
    primary_attribute = models.ForeignKey(Attribute, blank=True, null=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        verbose_name = _('QuestionSet')
        verbose_name_plural = _('QuestionSets')

    def __str__(self):
        return '%s / %s / %s / %s' % (self.catalog_title, self.section_title, self.subsection_title, self.title)

    @property
    def tag(self):
        return self.attributeset.tag if self.attributeset else None

    @property
    def is_collection(self):
        return self.attributeset.is_collection if self.attributeset else None


@python_2_unicode_compatible
class Question(QuestionEntity):

    WIDGET_TYPE_CHOICES = (
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('yesno', 'Yes/No'),
        ('checkbox', 'Checkboxes'),
        ('radio', 'Radio buttons'),
        ('select', 'Select drop-down'),
        ('range', 'Range slider'),
        ('date', 'Date picker'),
    )

    questionset = models.ForeignKey('QuestionSet', blank=True, null=True, related_name='questions')

    attribute = models.ForeignKey(Attribute, blank=True, null=True, on_delete=models.SET_NULL, related_name='questions')

    text_en = models.TextField()
    text_de = models.TextField()

    widget_type = models.CharField(max_length=12, choices=WIDGET_TYPE_CHOICES)

    class Meta:
        ordering = ('subsection__section__order', 'subsection__order',  'order')
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')

    def __str__(self):
        if self.title:
            return '%s / %s / %s / %s' % (self.catalog_title, self.section_title, self.subsection_title, self.title)
        else:
            return '%s / %s / %s / %s' % (self.catalog_title, self.section_title, self.subsection_title, self.text)

    @property
    def text(self):
        return self.trans('text')

    @property
    def tag(self):
        return self.attribute.tag if self.attribute else None

    @property
    def is_collection(self):
        return self.attribute.is_collection if self.attribute else None


@python_2_unicode_compatible
class Option(models.Model, TranslationMixin):

    question = models.ForeignKey('Question', related_name='options')
    order = models.IntegerField(null=True)

    key = models.SlugField()

    text_en = models.CharField(max_length=256)
    text_de = models.CharField(max_length=256)

    input_field = models.BooleanField()

    class Meta:
        ordering = ('question', 'order', )
        verbose_name = _('Option')
        verbose_name_plural = _('Options')

    def __str__(self):
        return '%s / %s' % (self.question, self.text)

    @property
    def text(self):
        return self.trans('text')


@python_2_unicode_compatible
class Condition(models.Model):

    RELATION_EQUAL = 'eq'
    RELATION_NOT_EQUAL = 'neq'
    RELATION_CONTAINS = 'contains'
    RELATION_GREATER_THAN = 'gt'
    RELATION_GREATER_THAN_EQUAL = 'gte'
    RELATION_LESSER_THAN = 'lt'
    RELATION_LESSER_THAN_EQUAL = 'lte'
    RELATION_CHOICES = (
        (RELATION_EQUAL, 'equal (==)'),
        (RELATION_NOT_EQUAL, 'not equal (!=)'),
        (RELATION_CONTAINS, 'contains'),
        (RELATION_GREATER_THAN, 'greater than (>)'),
        (RELATION_GREATER_THAN_EQUAL, 'greater than or equal (>=)'),
        (RELATION_LESSER_THAN, 'lesser than (<)'),
        (RELATION_LESSER_THAN_EQUAL, 'lesser than or equal (<=)'),
    )

    question_entity = models.ForeignKey('QuestionEntity', related_name='conditions')

    attribute = models.ForeignKey(Attribute, blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    relation = models.CharField(max_length=8, choices=RELATION_CHOICES)
    value = models.CharField(max_length=256)

    class Meta:
        verbose_name = _('Condition')
        verbose_name_plural = _('Conditions')

    def __str__(self):
        return self.question_entity.title
