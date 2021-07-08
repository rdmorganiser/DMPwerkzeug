from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from rdmo.core.models import Model, TranslationMixin
from rdmo.core.utils import copy_model, join_url

from .catalog import Catalog


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
        for questionset in self.questionsets.filter(questionset=None):
            questionset.copy(uri_prefix, questionset.key, section=section)

        return section

    @property
    def parent_fields(self):
        return ('catalog', )

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
        return catalog.key + '/' + key

    @classmethod
    def build_uri(cls, uri_prefix, path):
        assert path
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/questions/', path)
