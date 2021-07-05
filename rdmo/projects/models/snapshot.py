from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rdmo.core.models import Model

from ..managers import SnapshotManager


class Snapshot(Model):

    objects = SnapshotManager()

    project = models.ForeignKey(
        'Project', related_name='snapshots',
        on_delete=models.CASCADE, null=True,
        verbose_name=_('Project'),
        help_text=_('The project this snapshot belongs to.')
    )
    title = models.CharField(
        max_length=256,
        verbose_name=_('Title'),
        help_text=_('The title for this snapshot.')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('A description for this snapshot (optional).')
    )

    class Meta:
        ordering = ('project', '-created')
        verbose_name = _('Snapshot')
        verbose_name_plural = _('Snapshots')

    def __str__(self):
        return '%s / %s' % (self.project.title, self.title)

    def get_absolute_url(self):
        return reverse('project', kwargs={'pk': self.project.pk})

    def save(self, *args, **kwargs):
        # copy_values is set to True for creating new snapshots and to False for updating
        # for imports it is provided as kwarg (as False)
        copy_values = kwargs.pop('copy_values', self.pk is None)
        super().save()

        if copy_values:
            # loop over values without snapshot and save a copy with a fk to the snapshot
            for value in self.project.values.filter(snapshot=None):
                value.pk = None
                value.snapshot = self
                value.save()

                if value.file:
                    value.copy_file(value.file_name, value.file)

    def rollback(self):
        # remove all current values for this project
        self.project.values.filter(snapshot=None).delete()

        # remove the snapshot_id from this snapshots values so they are current values
        for value in self.values.all():
            value.snapshot = None
            value.save()

            if value.file:
                # here, it is ok that django_cleanup deletes the file
                value.file.save(value.file_name, value.file)

        # remove all snapshot created later and the current_snapshot
        # this also removes the values of these snapshots
        for snapshot in self.project.snapshots.filter(created__gte=self.created):
            snapshot.delete()
