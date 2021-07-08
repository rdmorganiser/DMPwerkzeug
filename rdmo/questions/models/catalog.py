from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _

from rdmo.core.models import Model, TranslationMixin
from rdmo.core.utils import copy_model, get_language_fields, join_url

from ..managers import CatalogManager


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
