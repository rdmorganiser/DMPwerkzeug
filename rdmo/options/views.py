import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView

from rdmo.core.exports import XMLResponse
from rdmo.core.utils import get_model_field_meta, render_to_format
from rdmo.core.views import CSRFViewMixin, ModelPermissionMixin

from .models import Option, OptionSet
from .renderers import OptionSetRenderer
from .serializers.export import OptionSetExportSerializer

log = logging.getLogger(__name__)


class OptionsView(ModelPermissionMixin, CSRFViewMixin, TemplateView):
    template_name = 'options/options.html'
    permission_required = 'options.view_option'

    def get_context_data(self, **kwargs):
        context = super(OptionsView, self).get_context_data(**kwargs)
        context['export_formats'] = settings.EXPORT_FORMATS
        context['meta'] = {
            'OptionSet': get_model_field_meta(OptionSet),
            'Option': get_model_field_meta(Option)
        }
        return context


class OptionsExportView(ModelPermissionMixin, ListView):
    model = OptionSet
    context_object_name = 'optionsets'
    permission_required = 'options.view_optionset'

    def render_to_response(self, context, **response_kwargs):
        format = self.kwargs.get('format')
        if format == 'xml':
            serializer = OptionSetExportSerializer(context['optionsets'], many=True)
            xml = OptionSetRenderer().render(serializer.data)
            return XMLResponse(xml, name='options')
        else:
            return render_to_format(self.request, format, _('Options'), 'options/options_export.html', context)
