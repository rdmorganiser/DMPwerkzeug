from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from rdmo.core.utils import copy_model, join_url


class Attribute(MPTTModel):

    uri = models.URLField(
        max_length=640, blank=True,
        verbose_name=_('URI'),
        help_text=_('The Uniform Resource Identifier of this attribute (auto-generated).')
    )
    uri_prefix = models.URLField(
        max_length=256,
        verbose_name=_('URI Prefix'),
        help_text=_('The prefix for the URI of this attribute.')
    )
    key = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Key'),
        help_text=_('The internal identifier of this attribute.')
    )
    path = models.CharField(
        max_length=512, db_index=True,
        verbose_name=_('Path'),
        help_text=_('The path part of the URI of this attribute (auto-generated).')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Comment'),
        help_text=_('Additional information about this attribute.')
    )
    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Designates whether this attribute (and it\'s descendants) can be changed.')
    )
    parent = TreeForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='children', db_index=True,
        verbose_name=_('Parent attribute'),
        help_text=_('Parent attribute in the domain model.')
    )

    class Meta:
        ordering = ('uri', )
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        self.path = self.build_path(self.key, self.parent)
        self.uri = self.build_uri(self.uri_prefix, self.path)
        super().save(*args, **kwargs)

        # recursively save children
        for child in self.children.all():
            child.save()

    def copy(self, uri_prefix, key, parent=None, rebuild=True):
        assert parent not in self.get_descendants(include_self=True)

        # copy the attribute
        attribute = copy_model(self, uri_prefix=uri_prefix, key=key, parent=parent or self.parent)

        # recursively copy children
        for child in self.children.all():
            child.copy(uri_prefix, child.key, parent=attribute, rebuild=False)

        # rebuild the mptt tree, but only for the initially copied attribute
        if rebuild:
            Attribute.objects.rebuild()

        return attribute

    @property
    def parent_fields(self):
        return ('parent', )

    @property
    def is_locked(self):
        return self.get_ancestors(include_self=True).filter(locked=True).exists()

    @classmethod
    def build_path(cls, key, parent):
        assert key
        path = key
        while parent:
            path = parent.key + '/' + path
            parent = parent.parent
        return path

    @classmethod
    def build_uri(cls, uri_prefix, path):
        assert path
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/domain/', path)
