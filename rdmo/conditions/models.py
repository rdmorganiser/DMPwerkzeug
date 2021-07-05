from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from rdmo.core.utils import copy_model, join_url
from rdmo.domain.models import Attribute


class Condition(models.Model):

    RELATION_EQUAL = 'eq'
    RELATION_NOT_EQUAL = 'neq'
    RELATION_CONTAINS = 'contains'
    RELATION_GREATER_THAN = 'gt'
    RELATION_GREATER_THAN_EQUAL = 'gte'
    RELATION_LESSER_THAN = 'lt'
    RELATION_LESSER_THAN_EQUAL = 'lte'
    RELATION_EMPTY = 'empty'
    RELATION_NOT_EMPTY = 'notempty'
    RELATION_CHOICES = (
        (RELATION_EQUAL, 'is equal to (==)'),
        (RELATION_NOT_EQUAL, 'is not equal to (!=)'),
        (RELATION_CONTAINS, 'contains'),
        (RELATION_GREATER_THAN, 'is greater than (>)'),
        (RELATION_GREATER_THAN_EQUAL, 'is greater than or equal (>=)'),
        (RELATION_LESSER_THAN, 'is lesser than (<)'),
        (RELATION_LESSER_THAN_EQUAL, 'is lesser than or equal (<=)'),
        (RELATION_EMPTY, 'is empty'),
        (RELATION_NOT_EMPTY, 'is not empty'),
    )

    uri = models.URLField(
        max_length=640, blank=True,
        verbose_name=_('URI'),
        help_text=_('The Uniform Resource Identifier of this condition (auto-generated).')
    )
    uri_prefix = models.URLField(
        max_length=256,
        verbose_name=_('URI Prefix'),
        help_text=_('The prefix for the URI of this condition.')
    )
    key = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Key'),
        help_text=_('The internal identifier of this condition.')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Comment'),
        help_text=_('Additional internal information about this condition.')
    )
    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Designates whether this condition can be changed.')
    )
    source = models.ForeignKey(
        Attribute, db_constraint=False, blank=True, null=True, on_delete=models.SET_NULL, related_name='conditions',
        verbose_name=_('Source'),
        help_text=_('The attribute of the value for this condition.')
    )
    relation = models.CharField(
        max_length=8, choices=RELATION_CHOICES,
        verbose_name=_('Relation'),
        help_text=_('The relation this condition is using.')
    )
    target_text = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Target (Text)'),
        help_text=_('If using a regular value, the text value this condition is checking against (for boolean values use 1 and 0).')
    )
    target_option = models.ForeignKey(
        'options.Option', db_constraint=False, blank=True, null=True, on_delete=models.SET_NULL, related_name='conditions',
        verbose_name=_('Target (Option)'),
        help_text=_('If using a value pointing to an option, the option this condition is checking against.')
    )

    class Meta:
        ordering = ('uri', )
        verbose_name = _('Condition')
        verbose_name_plural = _('Conditions')

    def __str__(self):
        return self.key

    def save(self, *args, **kwargs):
        self.uri = self.build_uri(self.uri_prefix, self.key)
        super().save(*args, **kwargs)

    def copy(self, uri_prefix, key):
        condition = copy_model(self, uri_prefix=uri_prefix, key=key, source=self.source, target_option=self.target_option)

        return condition

    @property
    def source_label(self):
        return self.source.uri

    @property
    def relation_label(self):
        return self.get_relation_display()

    @property
    def target_label(self):
        if self.target_option:
            return self.target_option.label
        else:
            return self.target_text

    @property
    def is_locked(self):
        return self.locked

    def resolve(self, values, set_prefix=None, set_index=None):
        source_values = filter(lambda value: value.attribute == self.source, values)

        if set_prefix is not None:
            source_values = filter(lambda value: value.set_prefix == set_prefix, source_values)

        if set_index is not None:
            source_values = filter(lambda value: value.set_index == int(set_index), source_values)

        source_values = list(source_values)
        if not source_values:
            # try one level higher
            if set_prefix:
                rpartition = set_prefix.rpartition('|')
                set_prefix, set_index = rpartition[0], int(rpartition[2])
                return self.resolve(values, set_prefix, set_index)

        if self.relation == self.RELATION_EQUAL:
            return self._resolve_equal(source_values)

        elif self.relation == self.RELATION_NOT_EQUAL:
            return not self._resolve_equal(source_values)

        elif self.relation == self.RELATION_CONTAINS:
            return self._resolve_contains(source_values)

        elif self.relation == self.RELATION_GREATER_THAN:
            return self._resolve_greater_than(source_values)

        elif self.relation == self.RELATION_GREATER_THAN_EQUAL:
            return self._resolve_greater_than_equal(source_values)

        elif self.relation == self.RELATION_LESSER_THAN:
            return self._resolve_lesser_than(source_values)

        elif self.relation == self.RELATION_LESSER_THAN_EQUAL:
            return self._resolve_lesser_than_equal(source_values)

        elif self.relation == self.RELATION_EMPTY:
            return not self._resolve_not_empty(source_values)

        elif self.relation == self.RELATION_NOT_EMPTY:
            return self._resolve_not_empty(source_values)

        else:
            return False

    def _resolve_equal(self, values):
        results = []

        for value in values:
            if self.target_option:
                results.append(value.option == self.target_option)
            else:
                results.append(value.text == self.target_text)

        return True in results

    def _resolve_contains(self, values):
        results = []

        for value in values:
            results.append(self.target_text in value.text)

        return True in results

    def _resolve_greater_than(self, values):

        for value in values:
            try:
                if float(value.text) > float(self.target_text):
                    return True
            except ValueError:
                pass

        return False

    def _resolve_greater_than_equal(self, values):

        for value in values:
            try:
                if float(value.text) >= float(self.target_text):
                    return True
            except ValueError:
                pass

        return False

    def _resolve_lesser_than(self, values):

        for value in values:
            try:
                if float(value.text) < float(self.target_text):
                    return True
            except ValueError:
                pass

        return False

    def _resolve_lesser_than_equal(self, values):

        for value in values:
            try:
                if float(value.text) <= float(self.target_text):
                    return True
            except ValueError:
                pass

        return False

    def _resolve_not_empty(self, values):

        for value in values:
            if bool(value.text) or bool(value.option):
                return True

        return False

    @classmethod
    def build_uri(cls, uri_prefix, key):
        assert key
        return join_url(uri_prefix or settings.DEFAULT_URI_PREFIX, '/conditions/', key)
