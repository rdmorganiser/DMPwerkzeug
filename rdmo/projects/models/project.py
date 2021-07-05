from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Exists, OuterRef
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from rdmo.core.models import Model
from rdmo.domain.models import Attribute
from rdmo.questions.models import Catalog, Question
from rdmo.tasks.models import Task
from rdmo.views.models import View

from ..managers import ProjectManager


class Project(MPTTModel, Model):

    objects = ProjectManager()

    parent = TreeForeignKey(
        'self', null=True, blank=True,
        on_delete=models.DO_NOTHING, related_name='children', db_index=True,
        verbose_name=_('Parent project'),
        help_text=_('The parent project of this project.')
    )
    user = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='Membership', related_name='projects',
        verbose_name=_('User'),
        help_text=_('The list of users for this project.')
    )
    site = models.ForeignKey(
        Site, on_delete=models.SET_NULL, null=True,
        verbose_name=_('Site'),
        help_text=_('The site this project belongs to (in a multi site setup).')
    )
    title = models.CharField(
        max_length=256,
        verbose_name=_('Title'),
        help_text=_('The title for this project.')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('A description for this project (optional).')
    )
    catalog = models.ForeignKey(
        Catalog, related_name='projects', on_delete=models.SET_NULL, null=True,
        verbose_name=_('Catalog'),
        help_text=_('The catalog which will be used for this project.')
    )
    tasks = models.ManyToManyField(
        Task, blank=True, through='Issue',
        verbose_name=_('Tasks'),
        help_text=_('The tasks that will be used for this project.')
    )
    views = models.ManyToManyField(
        View, blank=True,
        verbose_name=_('Views'),
        help_text=_('The views that will be used for this project.')
    )

    class Meta:
        ordering = ('tree_id', 'level', 'title')
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')

    class MPTTMeta:
        order_insertion_by = ('title', )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('project', kwargs={'pk': self.pk})

    def clean(self):
        if self.id and self.parent in self.get_descendants(include_self=True):
            raise ValidationError({
                'parent': [_('A project may not be moved to be a child of itself or one of its descendants.')]
            })

    @property
    def progress(self):
        # create a queryset for the attributes of the catalog for this project
        # the subquery is used to query only attributes which have a question in the catalog, which is not optional
        questions = Question.objects.filter(attribute_id=OuterRef('pk'), questionset__section__catalog_id=self.catalog.id) \
                                    .exclude(is_optional=True)
        attributes = Attribute.objects.annotate(active=Exists(questions)).filter(active=True).distinct()

        # query the total number of attributes from the qs above
        total = attributes.count()

        # query all current values with attributes from the qs above, but where the text, option, or file field is set,
        # and count only one value per attribute
        values = self.values.filter(snapshot=None) \
                            .filter(attribute__in=attributes) \
                            .exclude((models.Q(text='') | models.Q(text=None)) & models.Q(option=None) &
                                     (models.Q(file='') | models.Q(file=None))) \
                            .distinct().values('attribute').count()

        try:
            ratio = values / total
        except ZeroDivisionError:
            ratio = 0

        return {
            'total': total,
            'values': values,
            'ratio': ratio
        }

    @cached_property
    def member(self):
        return self.user.all()

    @cached_property
    def owners_str(self):
        return ', '.join(['' if x is None else str(x) for x in self.user.filter(membership__role='owner')])

    @cached_property
    def owners(self):
        return self.user.filter(memberships__role='owner')

    @cached_property
    def managers(self):
        return self.user.filter(memberships__role='manager')

    @cached_property
    def authors(self):
        return self.user.filter(memberships__role='author')

    @cached_property
    def guests(self):
        return self.user.filter(memberships__role='guest')

    @property
    def file_size(self):
        queryset = self.values.filter(snapshot=None).exclude(models.Q(file='') | models.Q(file=None))
        return sum([value.file.size for value in queryset])


@receiver(pre_delete, sender=Project)
def reparent_children(sender, instance, **kwargs):
    for child in instance.get_children():
        child.move_to(instance.parent, 'last-child')
        child.save()
