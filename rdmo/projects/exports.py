import re

from django.http import HttpResponse

from rdmo.core.exports import prettify_xml
from rdmo.core.plugins import Plugin
from rdmo.core.utils import render_to_csv
from rdmo.questions.models import Question

from .renderers import XMLRenderer
from .serializers.export import ProjectSerializer as ExportSerializer


class Export(Plugin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.project = None
        self.snapshot = None

    def render(self):
        raise NotImplementedError

    def get_set(self, path, set_prefix=''):
        return self.project.values.filter(snapshot=self.snapshot, attribute__path=path, set_prefix=set_prefix) \
                                  .order_by('set_index', 'collection_index')

    def get_values(self, path, set_prefix='', set_index=0):
        return self.project.values.filter(snapshot=self.snapshot, attribute__path=path, set_prefix=set_prefix, set_index=set_index) \
                                  .order_by('collection_index')

    def get_value(self, path, set_prefix='', set_index=0, collection_index=0):
        try:
            return self.get_values(path, set_prefix=set_prefix, set_index=set_index)[collection_index]
        except IndexError:
            return None

    def get_text(self, path, set_prefix='', set_index=0, collection_index=0):
        try:
            return self.get_values(path, set_prefix=set_prefix, set_index=set_index)[collection_index].text
        except IndexError:
            return None

    def get_timestamp(self, path, set_prefix='', set_index=0, collection_index=0):
        try:
            return self.get_values(path, set_prefix=set_prefix, set_index=set_index)[collection_index].value.isoformat()
        except (IndexError, AttributeError):
            return None

    def get_year(self, path, set_prefix='', set_index=0, collection_index=0):
        try:
            return self.get_values(path, set_prefix=set_prefix, set_index=set_index)[collection_index].value.year
        except (IndexError, AttributeError):
            return None

    def get_list(self, path, set_prefix='', set_index=0):
        values = self.get_values(path, set_prefix=set_prefix, set_index=set_index)
        return [value.text for value in values if value.text]

    def get_bool(self, path, set_prefix='', set_index=0, collection_index=0):
        value = self.get_value(path, set_prefix=set_prefix, set_index=set_index, collection_index=collection_index)
        if value:
            return True if value.text == '1' else False
        else:
            return None

    def get_option(self, options, path, set_prefix='', set_index=0, collection_index=0, default=None):
        value = self.get_value(path, set_prefix=set_prefix, set_index=set_index, collection_index=collection_index)
        if value and value.option:
            # lookup option dict in class
            return options.get(value.option.path, default)
        else:
            return default


class CSVExport(Export):

    delimiter = ','

    def render(self):
        queryset = self.project.values.filter(snapshot=None)
        data = []

        for question in Question.objects.order_by_catalog(self.project.catalog):
            if question.questionset.is_collection and question.questionset.attribute:
                if question.questionset.attribute.uri.endswith('/id'):
                    set_attribute_uri = question.questionset.attribute
                else:
                    set_attribute_uri = question.questionset.attribute.uri.rstrip('/') + '/id'

                for value_set in queryset.filter(attribute__uri=set_attribute_uri):
                    values = queryset.filter(attribute=question.attribute, set_index=value_set.set_index) \
                                     .order_by('set_prefix', 'set_index', 'collection_index')
                    data.append((self.stringify(question.text), self.stringify(value_set.value), self.stringify_values(values)))
            else:
                values = queryset.filter(attribute=question.attribute).order_by('set_prefix', 'set_index', 'collection_index')

                data.append((self.stringify(question.text), '', self.stringify_values(values)))

        return render_to_csv(self.project.title, data, self.delimiter)

    def stringify_values(self, values):
        if values is not None:
            return '; '.join([self.stringify(value.value_and_unit) for value in values])
        else:
            return ''

    def stringify(self, el):
        if el is None:
            return ''
        else:
            return re.sub(r'\s+', ' ', str(el))


class CSVCommaExport(CSVExport):
    delimiter = ','


class CSVSemicolonExport(CSVExport):
    delimiter = ';'


class RDMOXMLExport(Export):

    def render(self):
        serializer = ExportSerializer(self.project)
        xmldata = XMLRenderer().render(serializer.data)
        response = HttpResponse(prettify_xml(xmldata), content_type="application/xml")
        response['Content-Disposition'] = 'filename="%s.xml"' % self.project.title
        return response
