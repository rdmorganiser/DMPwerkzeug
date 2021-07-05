import logging

from django.db import models
from django.utils.timezone import now
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from rdmo.core.utils import get_languages

logger = logging.getLogger(__name__)


class Model(models.Model):

    created = models.DateTimeField(editable=False, verbose_name=_('created'))
    updated = models.DateTimeField(editable=False, verbose_name=_('updated'))

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = now()

        self.updated = now()

        super(Model, self).save(*args, **kwargs)


class TranslationMixin(object):

    def trans(self, field):
        current_language = get_language()

        languages = get_languages()
        for lang_code, lang_string, lang_field in languages:
            if lang_code == current_language:
                r = getattr(self, '%s_%s' % (field, lang_field)) or None
                if r is not None:
                    return r
                else:
                    for i in range(1, 6):
                        r = getattr(self, '%s_%s' % (field, 'lang' + str(i))) or None
                        if r is not None:
                            return r
        return ''
