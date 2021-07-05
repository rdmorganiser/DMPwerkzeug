import logging

from django.conf import settings
from django.db.models import Prefetch
from django.views.generic import DetailView, TemplateView

from rdmo.core.exports import XMLResponse
from rdmo.core.utils import get_model_field_meta, render_to_format
from rdmo.core.views import CSRFViewMixin, ModelPermissionMixin

from .models import Catalog, Question, QuestionSet, Section
from .renderers import CatalogRenderer
from .serializers.export import CatalogExportSerializer

log = logging.getLogger(__name__)


class CatalogsView(ModelPermissionMixin, CSRFViewMixin, TemplateView):
    template_name = 'questions/catalogs.html'
    permission_required = 'questions.view_catalog'

    def get_context_data(self, **kwargs):
        context = super(CatalogsView, self).get_context_data(**kwargs)
        context['export_formats'] = settings.EXPORT_FORMATS
        context['meta'] = {
            'Catalog': get_model_field_meta(Catalog),
            'Section': get_model_field_meta(Section),
            'QuestionSet': get_model_field_meta(QuestionSet),
            'Question': get_model_field_meta(Question),
        }
        return context


class CatalogExportView(ModelPermissionMixin, DetailView):
    model = Catalog
    context_object_name = 'catalog'
    permission_required = 'questions.view_catalog'

    def get_queryset(self):
        return Catalog.objects.prefetch_related(
            'sections',
            Prefetch('sections__questionsets', queryset=QuestionSet.objects.filter(questionset=None).prefetch_related(
                'conditions',
                'questions',
                'questions__attribute',
                'questions__optionsets',
                'questionsets',
                'questionsets__attribute',
                'questionsets__conditions',
                'questionsets__questions',
                'questionsets__questions__attribute',
                'questionsets__questions__optionsets',
                'questionsets__questionsets'
            ).select_related('attribute'))
        )

    def render_to_response(self, context, **response_kwargs):
        format = self.kwargs.get('format')
        if format == 'xml':
            serializer = CatalogExportSerializer(context['catalog'])
            xml = CatalogRenderer().render([serializer.data])
            return XMLResponse(xml, name=context['catalog'].key)
        else:
            return render_to_format(self.request, format, context['catalog'].title, 'questions/catalog_export.html', context)
