from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from rdmo.conditions.models import Condition
from rdmo.core.models import TranslationMixin
from rdmo.core.plugins import get_plugin
from rdmo.core.utils import copy_model, join_url


class OptionSet(models.Model):

    uri = models.URLField(
        max_length=640, blank=True,
        verbose_name=_('URI'),
        help_text=_('The Uniform Resource Identifier of this option set (auto-generated).')
    )
    uri_prefix = models.URLField(
        max_length=256,
        verbose_name=_('URI Prefix'),
        help_text=_('The prefix for the URI of this option set.')
    )
    key = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Key'),
        help_text=_('The internal identifier of this option set.')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Comment'),
        help_text=_('Additional internal information about this option set.')
    )
    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Designates whether this option set (and it\'s options) can be changed.')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('The position of this option set in lists.')
    )
    provider_key = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Provider'),
        help_text=_('The provider for this optionset. If set, it will create dynamic options for this optionset.')
    )
    conditions = models.ManyToManyField(
        Condition, blank=True, related_name='optionsets',
        verbose_name=_('Conditions'),
        help_text=_('The list of conditions evaluated for this option set.')
    )

    class Meta:
        ordering = ('uri', )
        verbose_name = _('Option set')
        verbose_name_plural = _('Option sets')

    def __str__(self):
        return self.key

    def save(self, *args, **kwargs):
        self.uri = self.build_uri(self.uri_prefix, self.key)
        super().save(*args, **kwargs)

        for option in self.options.all():
            option.save()

    def copy(self, uri_prefix, key):
        optionset = copy_model(self, uri_prefix=uri_prefix, key=key)

        # copy m2m fields
        optionset.conditions.set(self.conditions.all())

        # copy children
        for option in self.options.all():
            option.copy(uri_prefix, option.key, optionset=optionset)

        return optionset

    @property
    def label(self):
        return self.uri

    @property
    def provider(self):
        return get_plugin('OPTIONSET_PROVIDERS', self.provider_key)

    @property
    def has_provider(self):
        return self.provider is not None

    @property
    def has_search(self):
        return self.has_provider and self.provider.search

    @property
    def has_conditions(self):
        return self.conditions.exists()

    @property
    def is_locked(self):
        return self.locked

    @classmethod
    def build_uri(cls, uri_prefix, key):
        assert key
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/options/', key)


class Option(models.Model, TranslationMixin):

    uri = models.URLField(
        max_length=640, blank=True,
        verbose_name=_('URI'),
        help_text=_('The Uniform Resource Identifier of this option (auto-generated).')
    )
    uri_prefix = models.URLField(
        max_length=256,
        verbose_name=_('URI Prefix'),
        help_text=_('The prefix for the URI of this option.')
    )
    key = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Key'),
        help_text=_('The internal identifier of this option.')
    )
    path = models.SlugField(
        max_length=512, blank=True,
        verbose_name=_('Path'),
        help_text=_('The path part of the URI for this option (auto-generated).')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Comment'),
        help_text=_('Additional internal information about this option.')
    )
    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Designates whether this option can be changed.')
    )
    optionset = models.ForeignKey(
        'OptionSet', on_delete=models.CASCADE, related_name='options',
        verbose_name=_('Option set'),
        help_text=_('The option set this option belongs to.')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('Position in lists.')
    )
    text_lang1 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (primary)'),
        help_text=_('The text for this option in the primary language.')
    )
    text_lang2 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (secondary)'),
        help_text=_('The text for this option in the secondary language.')
    )
    text_lang3 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (tertiary)'),
        help_text=_('The text for this option in the tertiary language.')
    )
    text_lang4 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (quaternary)'),
        help_text=_('The text for this option in the quaternary language.')
    )
    text_lang5 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (quinary)'),
        help_text=_('The text for this option in the quinary language.')
    )
    additional_input = models.BooleanField(
        default=False,
        verbose_name=_('Additional input'),
        help_text=_('Designates whether an additional input is possible for this option.')
    )

    class Meta:
        ordering = ('optionset__order', 'optionset__key', 'order', 'key')
        verbose_name = _('Option')
        verbose_name_plural = _('Options')

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        self.path = self.build_path(self.key, self.optionset)
        self.uri = self.build_uri(self.uri_prefix, self.path)
        super().save(*args, **kwargs)

    def copy(self, uri_prefix, key, optionset=None):
        return copy_model(self, uri_prefix=uri_prefix, key=key, optionset=optionset or self.optionset)

    @property
    def parent_fields(self):
        return ('optionset', )

    @property
    def text(self):
        return self.trans('text')

    @property
    def label(self):
        return '%s ("%s")' % (self.uri, self.text)

    @property
    def is_locked(self):
        return self.locked or self.optionset.locked

    @classmethod
    def build_path(cls, key, optionset):
        assert key
        assert optionset
        return '%s/%s' % (optionset.key, key) if (optionset and key) else None

    @classmethod
    def build_uri(cls, uri_prefix, path):
        assert path
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/options/', path)
