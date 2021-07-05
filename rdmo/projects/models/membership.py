from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..managers import MembershipManager


class Membership(models.Model):

    objects = MembershipManager()

    ROLE_CHOICES = (
        ('owner', _('Owner')),
        ('manager', _('Manager')),
        ('author', _('Author')),
        ('guest', _('Guest')),
    )

    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, related_name='memberships',
        verbose_name=_('Project'),
        help_text=_('The project for this membership.')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships',
        verbose_name=_('User'),
        help_text=_('The user for this membership.')
    )
    role = models.CharField(
        max_length=12, choices=ROLE_CHOICES,
        verbose_name=_('Role'),
        help_text=_('The role for this membership.')
    )

    class Meta:
        ordering = ('project__title', )
        verbose_name = _('Membership')
        verbose_name_plural = _('Memberships')

    def __str__(self):
        return '%s / %s / %s' % (self.project.title, self.user.username, self.role)

    def get_absolute_url(self):
        return reverse('project', kwargs={'pk': self.project.pk})

    @property
    def is_last_owner(self):
        return not Membership.objects.filter(project=self.project, role='owner').exclude(user=self.user).exists()
