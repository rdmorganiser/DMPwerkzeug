import logging

from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import redirect
from django.views.generic import DetailView

from rdmo.core.constants import VALUE_TYPE_FILE
from rdmo.core.utils import render_to_format
from rdmo.core.views import ObjectPermissionMixin
from rdmo.questions.models import QuestionSet, Question
from rdmo.views.utils import ProjectWrapper

from ..models import Project, Snapshot
from ..utils import get_value_path
logger = logging.getLogger(__name__)


class ProjectAnswersView(ObjectPermissionMixin, DetailView):
    model = Project
    queryset = Project.objects.prefetch_related(
        Prefetch('catalog__sections__questionsets', queryset=QuestionSet.objects.select_related('attribute')),
        Prefetch('catalog__sections__questionsets__questions', queryset=Question.objects.select_related('attribute', 'questionset')),
        Prefetch('catalog__sections__questionsets__questionsets', queryset=QuestionSet.objects.select_related('attribute')),
        Prefetch('catalog__sections__questionsets__questionsets__questions', queryset=Question.objects.select_related('attribute', 'questionset')),
    )

    permission_required = 'projects.view_project_object'
    template_name = 'projects/project_answers.html'
    no_catalog_error_template = 'projects/project_error_no_catalog.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.catalog is None:
            return redirect('project_error', pk=self.object.pk)
        else:
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            context['current_snapshot'] = context['project'].snapshots.get(pk=self.kwargs.get('snapshot_id'))
        except Snapshot.DoesNotExist:
            context['current_snapshot'] = None

        # collect values with files, remove double files and order them.
        context['attachments'] = context['project'].values.filter(snapshot=context['current_snapshot']) \
                                                          .filter(value_type=VALUE_TYPE_FILE) \
                                                          .order_by('file')

        context.update({
            'project_wrapper': ProjectWrapper(context['project'], context['current_snapshot']),
            'snapshots': list(context['project'].snapshots.values('id', 'title')),
            'export_formats': settings.EXPORT_FORMATS
        })

        return context


class ProjectAnswersExportView(ObjectPermissionMixin, DetailView):
    model = Project
    queryset = Project.objects.prefetch_related(
        Prefetch('catalog__sections__questionsets', queryset=QuestionSet.objects.select_related('attribute')),
        Prefetch('catalog__sections__questionsets__questions', queryset=Question.objects.select_related('attribute', 'questionset')),
        Prefetch('catalog__sections__questionsets__questionsets', queryset=QuestionSet.objects.select_related('attribute')),
        Prefetch('catalog__sections__questionsets__questionsets__questions', queryset=Question.objects.select_related('attribute', 'questionset')),
    )
    permission_required = 'projects.view_project_object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            context['current_snapshot'] = context['project'].snapshots.get(pk=self.kwargs.get('snapshot_id'))
        except Snapshot.DoesNotExist:
            context['current_snapshot'] = None

        context.update({
            'project_wrapper': ProjectWrapper(context['project'], context['current_snapshot']),
            'title': context['project'].title,
            'format': self.kwargs.get('format'),
            'resource_path': get_value_path(context['project'], context['current_snapshot'])
        })

        return context

    def render_to_response(self, context, **response_kwargs):
        return render_to_format(self.request, context['format'], context['title'], 'projects/project_answers_export.html', context)
