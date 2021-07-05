from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from rdmo.core.models import TranslationMixin


class AdditionalField(models.Model, TranslationMixin):

    TYPE_CHOICES = (
        ('text', 'Text'),
        ('textarea', 'Textarea'),
    )

    key = models.SlugField()
    type = models.CharField(max_length=11, choices=TYPE_CHOICES)

    text_lang1 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (primary)'),
        help_text=_('The text for this additional field in the primary language.')
    )
    text_lang2 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (secondary)'),
        help_text=_('The text for this additional field in the secondary language.')
    )
    text_lang3 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (tertiary)'),
        help_text=_('The text for this additional field in the tertiary language.')
    )
    text_lang4 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (quaternary)'),
        help_text=_('The text for this additional field in the quaternary language.')
    )
    text_lang5 = models.CharField(
        max_length=256, blank=True,
        verbose_name=_('Text (quinary)'),
        help_text=_('The text for this additional field in the quinary language.')
    )
    help_lang1 = models.TextField(
        blank=True,
        verbose_name=_('Help (primary)'),
        help_text=_('The help text to be displayed next to the input element in the primary language.')
    )
    help_lang2 = models.TextField(
        blank=True,
        verbose_name=_('Help (secondary)'),
        help_text=_('The help text to be displayed next to the input element in the secondary language.')
    )
    help_lang3 = models.TextField(
        blank=True,
        verbose_name=_('Help (tertiary)'),
        help_text=_('The help text to be displayed next to the input element in the tertiary language.')
    )
    help_lang4 = models.TextField(
        blank=True,
        verbose_name=_('Help (quaternary)'),
        help_text=_('The help text to be displayed next to the input element in the quaternary language.')
    )
    help_lang5 = models.TextField(
        blank=True,
        verbose_name=_('Help (quinary)'),
        help_text=_('The help text to be displayed next to the input element in the quinary language.')
    )
    required = models.BooleanField(
        verbose_name=_('Required'),
        help_text=_('Designates whether this additional field is required.')
    )

    class Meta:
        ordering = ('key',)
        verbose_name = _('Additional field')
        verbose_name_plural = _('Additional fields')

    def __str__(self):
        return self.text

    @property
    def text(self):
        return self.trans('text')

    @property
    def help(self):
        return self.trans('help')


class AdditionalFieldValue(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='additional_values')
    field = models.ForeignKey(AdditionalField, on_delete=models.CASCADE, related_name='+')
    value = models.CharField(max_length=256)

    class Meta:
        ordering = ('user', 'field')

        verbose_name = _('Additional field value')
        verbose_name_plural = _('Additional field values')

    def __str__(self):
        return self.user.username + '/' + self.field.key


class ConsentFieldValue(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    consent = models.BooleanField(
        default=False,
        help_text='Designates whether the user has agreed to the terms of use.',
        verbose_name='Consent'
    )

    class Meta:
        ordering = ('user', )
        verbose_name = _('Consent field value')
        verbose_name_plural = _('Consent field values')

    def __str__(self):
        return self.user.username


class Role(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    member = models.ManyToManyField(
        Site, related_name='members', blank=True,
        verbose_name=_('Member'),
        help_text=_('The sites for which this user is a member.')
    )
    manager = models.ManyToManyField(
        Site, related_name='managers', blank=True,
        verbose_name=_('Manager'),
        help_text=_('The sites for which this user is manager.')
    )

    class Meta:
        ordering = ('user', )
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def post_save_user(sender, **kwargs):
    if not kwargs.get('raw', False):
        user = kwargs['instance']
        current_site = Site.objects.get_current()

        try:
            role = user.role
        except Role.DoesNotExist:
            role = Role(user=user)
            role.save()

        if current_site not in role.member.all():
            role.member.add(current_site)
