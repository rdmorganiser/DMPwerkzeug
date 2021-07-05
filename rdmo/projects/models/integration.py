from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rdmo.core.plugins import get_plugin

from ..managers import IntegrationManager


class Integration(models.Model):

    objects = IntegrationManager()

    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, related_name='integrations',
        verbose_name=_('Project'),
        help_text=_('The project for this integration.')
    )
    provider_key = models.TextField(
        verbose_name=_('Provider key'),
        help_text=_('The key of the provider for this integration.')
    )

    class Meta:
        ordering = ('project__title', )
        verbose_name = _('Integration')
        verbose_name_plural = _('Integrations')

    def __str__(self):
        return '%s / %s' % (self.project.title, self.provider_key)

    @property
    def provider(self):
        return get_plugin('SERVICE_PROVIDERS', self.provider_key)

    def get_absolute_url(self):
        return reverse('project', kwargs={'pk': self.project.pk})

    def save_options(self, options):
        for field in self.provider.fields:
            try:
                integration_option = IntegrationOption.objects.get(integration=self, key=field.get('key'))
            except IntegrationOption.DoesNotExist:
                integration_option = IntegrationOption(integration=self, key=field.get('key'))

            integration_option.value = options.get(field.get('key')) or ''  # required was (hopefully) checked before
            integration_option.secret = field.get('secret', False)
            integration_option.save()


class IntegrationOption(models.Model):

    integration = models.ForeignKey(
        'Integration', on_delete=models.CASCADE, related_name='options',
        verbose_name=_('Integration'),
        help_text=_('The integration for this integration option.')
    )
    key = models.SlugField(
        max_length=128,
        verbose_name=_('Key'),
        help_text=_('The key for this integration option.')
    )
    value = models.TextField(
        verbose_name=_('Value'),
        help_text=_('The value for this integration option.')
    )
    secret = models.BooleanField(
        default=False,
        verbose_name=_('Secret'),
        help_text=_('Designates whether this integration option is hidden from regular users.')
    )

    class Meta:
        ordering = ('integration__project__title', )
        verbose_name = _('Integration option')
        verbose_name_plural = _('Integration options')

    def __str__(self):
        return '%s / %s / %s = %s' % (self.integration.project.title, self.integration.provider_key, self.key, self.value)
