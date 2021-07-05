from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy as _


class Overlay(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='overlays',
        verbose_name=_('User'),
        help_text=_('The user for this overlay.')
    )
    site = models.ForeignKey(
        Site, on_delete=models.SET_NULL, null=True,
        verbose_name=_('Site'),
        help_text=_('The site for this overlay.')
    )
    url_name = models.SlugField(
        max_length=128,
        verbose_name=_('Url name'),
        help_text=_('The url_name for this overlay.')
    )
    current = models.SlugField(
        max_length=128, blank=True,
        verbose_name=_('Current'),
        help_text=_('The current state for this overlay.')
    )

    class Meta:
        ordering = ('user', 'url_name')
        verbose_name = _('Overlay')
        verbose_name_plural = _('Overlays')

    def __str__(self):
        return '{} / {}'.format(self.user, self.url_name)
