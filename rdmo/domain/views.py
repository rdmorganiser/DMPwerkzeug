import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView
from rdmo.core.exports import XMLResponse
from rdmo.core.utils import (get_model_field_meta, render_to_csv,
                             render_to_format)
from rdmo.core.views import CSRFViewMixin, ModelPermissionMixin

from .models import Attribute
from .renderers import AttributeRenderer
from .serializers.export import AttributeExportSerializer

logger = logging.getLogger(__name__)


class DomainView(ModelPermissionMixin, CSRFViewMixin, TemplateView):
    template_name = 'domain/domain.html'
    permission_required = 'domain.view_attribute'

    def get_context_data(self, **kwargs):
        context = super(DomainView, self).get_context_data(**kwargs)
        context['export_formats'] = settings.EXPORT_FORMATS
        context['meta'] = {
            'Attribute': get_model_field_meta(Attribute)
        }
        return context


class DomainExportView(ModelPermissionMixin, ListView):
    model = Attribute
    context_object_name = 'attributes'
    permission_required = 'domain.view_attribute'

    def render_to_response(self, context, **response_kwargs):
        format = self.kwargs.get('format')
        if format == 'xml':
            serializer = AttributeExportSerializer(context['attributes'], many=True)
            xml = AttributeRenderer().render(serializer.data)
            return XMLResponse(xml, name='domain')
        elif format[:3] == 'csv':
            if format == 'csvcomma':
                delimiter = ','
            else:
                delimiter = ';'
            rows = []
            for attribute in context['attributes']:
                rows.append((
                    attribute.key,
                    attribute.comment,
                    attribute.uri
                ))
            return render_to_csv(_('Domain'), rows, delimiter)
        else:
            return render_to_format(self.request, format, _('Domain'), 'domain/domain_export.html', context)
