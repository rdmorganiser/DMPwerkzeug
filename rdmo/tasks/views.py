import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView

from rdmo.core.exports import XMLResponse
from rdmo.core.utils import get_model_field_meta, render_to_format
from rdmo.core.views import CSRFViewMixin, ModelPermissionMixin

from .models import Task
from .renderers import TaskRenderer
from .serializers.export import TaskExportSerializer

log = logging.getLogger(__name__)


class TasksView(ModelPermissionMixin, CSRFViewMixin, TemplateView):
    template_name = 'tasks/tasks.html'
    permission_required = 'tasks.view_task'

    def get_context_data(self, **kwargs):
        context = super(TasksView, self).get_context_data(**kwargs)
        context['export_formats'] = settings.EXPORT_FORMATS
        context['meta'] = {
            'Task': get_model_field_meta(Task)
        }
        return context


class TasksExportView(ModelPermissionMixin, ListView):
    model = Task
    context_object_name = 'tasks'
    permission_required = 'tasks.view_task'

    def render_to_response(self, context, **response_kwargs):
        format = self.kwargs.get('format')
        if format == 'xml':
            serializer = TaskExportSerializer(context['tasks'], many=True)
            xml = TaskRenderer().render(serializer.data)
            return XMLResponse(xml, name='tasks')
        else:
            return render_to_format(self.request, format, _('Tasks'), 'tasks/tasks_export.html', context)
