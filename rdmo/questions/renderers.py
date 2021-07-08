from rdmo.core.renderers import BaseXMLRenderer
from rdmo.core.utils import get_languages


class XMLRenderer(BaseXMLRenderer):

    def render_catalog(self, xml, catalog):
        xml.startElement('catalog', {'dc:uri': catalog['uri']})
        self.render_text_element(xml, 'uri_prefix', {}, catalog['uri_prefix'])
        self.render_text_element(xml, 'key', {}, catalog['key'])
        self.render_text_element(xml, 'dc:comment', {}, catalog['comment'])
        self.render_text_element(xml, 'order', {}, catalog['order'])

        for lang_code, lang_string, lang_field in get_languages():
            self.render_text_element(xml, 'title', {'lang': lang_code}, catalog['title_%s' % lang_code])

        xml.endElement('catalog')

        if 'sections' in catalog and catalog['sections']:
            for section in catalog['sections']:
                self.render_section(xml, section)

    def render_section(self, xml, section):
        xml.startElement('section', {'dc:uri': section['uri']})
        self.render_text_element(xml, 'uri_prefix', {}, section['uri_prefix'])
        self.render_text_element(xml, 'key', {}, section['key'])
        self.render_text_element(xml, 'path', {}, section['path'])
        self.render_text_element(xml, 'dc:comment', {}, section['comment'])
        self.render_text_element(xml, 'catalog', {'dc:uri': section['catalog']}, None)
        self.render_text_element(xml, 'order', {}, section['order'])

        for lang_code, lang_string, lang_field in get_languages():
            self.render_text_element(xml, 'title', {'lang': lang_code}, section['title_%s' % lang_code])

        xml.endElement('section')

        if 'questionsets' in section and section['questionsets']:
            for questionset in section['questionsets']:
                self.render_questionset(xml, questionset)

    def render_questionset(self, xml, questionset):
        xml.startElement('questionset', {'dc:uri': questionset['uri']})
        self.render_text_element(xml, 'uri_prefix', {}, questionset['uri_prefix'])
        self.render_text_element(xml, 'key', {}, questionset['key'])
        self.render_text_element(xml, 'path', {}, questionset['path'])
        self.render_text_element(xml, 'dc:comment', {}, questionset['comment'])
        self.render_text_element(xml, 'attribute', {'dc:uri': questionset['attribute']}, None)
        self.render_text_element(xml, 'section', {'dc:uri': questionset['section']}, None)
        self.render_text_element(xml, 'questionset', {'dc:uri': questionset['questionset']}, None)
        self.render_text_element(xml, 'is_collection', {}, questionset['is_collection'])
        self.render_text_element(xml, 'order', {}, questionset['order'])

        for lang_code, lang_string, lang_field in get_languages():
            self.render_text_element(xml, 'title', {'lang': lang_code}, questionset['title_%s' % lang_code])
            self.render_text_element(xml, 'help', {'lang': lang_code}, questionset['help_%s' % lang_code])
            self.render_text_element(xml, 'verbose_name', {'lang': lang_code}, questionset['verbose_name_%s' % lang_code])
            self.render_text_element(xml, 'verbose_name_plural', {'lang': lang_code}, questionset['verbose_name_plural_%s' % lang_code])

        xml.startElement('conditions', {})
        if 'conditions' in questionset and questionset['conditions']:
            for condition in questionset['conditions']:
                self.render_text_element(xml, 'condition', {'dc:uri': condition}, None)
        xml.endElement('conditions')

        xml.endElement('questionset')

        if 'questionsets' in questionset and questionset['questionsets']:
            for qs in questionset['questionsets']:
                self.render_questionset(xml, qs)

        if 'questions' in questionset and questionset['questions']:
            for question in questionset['questions']:
                self.render_question(xml, question)

    def render_question(self, xml, question):
        xml.startElement('question', {'dc:uri': question['uri']})
        self.render_text_element(xml, 'uri_prefix', {}, question['uri_prefix'])
        self.render_text_element(xml, 'key', {}, question['key'])
        self.render_text_element(xml, 'path', {}, question['path'])
        self.render_text_element(xml, 'dc:comment', {}, question['comment'])
        self.render_text_element(xml, 'attribute', {'dc:uri': question['attribute']}, None)
        self.render_text_element(xml, 'questionset', {'dc:uri': question['questionset']}, None)
        self.render_text_element(xml, 'is_collection', {}, question['is_collection'])
        self.render_text_element(xml, 'is_optional', {}, question['is_optional'])
        self.render_text_element(xml, 'order', {}, question['order'])

        for lang_code, lang_string, lang_field in get_languages():
            self.render_text_element(xml, 'help', {'lang': lang_code}, question['help_%s' % lang_code])
            self.render_text_element(xml, 'text', {'lang': lang_code}, question['text_%s' % lang_code])
            self.render_text_element(xml, 'default_text', {'lang': lang_code}, question['default_text_%s' % lang_code])
            self.render_text_element(xml, 'verbose_name', {'lang': lang_code}, question['verbose_name_%s' % lang_code])
            self.render_text_element(xml, 'verbose_name_plural', {'lang': lang_code}, question['verbose_name_plural_%s' % lang_code])

        self.render_text_element(xml, 'default_option', {'dc:uri': question['default_option']}, None)
        self.render_text_element(xml, 'default_external_id', {}, question['default_external_id'])

        self.render_text_element(xml, 'widget_type', {}, question['widget_type'])
        self.render_text_element(xml, 'value_type', {}, question['value_type'])
        self.render_text_element(xml, 'maximum', {}, question['maximum'])
        self.render_text_element(xml, 'minimum', {}, question['minimum'])
        self.render_text_element(xml, 'step', {}, question['step'])
        self.render_text_element(xml, 'unit', {}, question['unit'])
        self.render_text_element(xml, 'width', {}, question['width'])

        xml.startElement('optionsets', {})
        if 'optionsets' in question and question['optionsets']:
            for optionset in question['optionsets']:
                self.render_text_element(xml, 'optionset', {'dc:uri': optionset}, None)
        xml.endElement('optionsets')

        xml.startElement('conditions', {})
        if 'conditions' in question and question['conditions']:
            for condition in question['conditions']:
                self.render_text_element(xml, 'condition', {'dc:uri': condition}, None)
        xml.endElement('conditions')

        xml.endElement('question')


class CatalogRenderer(XMLRenderer):

    def render_document(self, xml, catalogs):
        xml.startElement('rdmo', {
            'xmlns:dc': 'http://purl.org/dc/elements/1.1/'
        })
        for catalog in catalogs:
            self.render_catalog(xml, catalog)
        xml.endElement('rdmo')


class SectionRenderer(XMLRenderer):

    def render_document(self, xml, sections):
        xml.startElement('rdmo', {
            'xmlns:dc': 'http://purl.org/dc/elements/1.1/'
        })
        for section in sections:
            self.render_section(xml, section)
        xml.endElement('rdmo')


class QuestionSetRenderer(XMLRenderer):

    def render_document(self, xml, questionsets):
        xml.startElement('rdmo', {
            'xmlns:dc': 'http://purl.org/dc/elements/1.1/'
        })
        for questionset in questionsets:
            self.render_questionset(xml, questionset)
        xml.endElement('rdmo')


class QuestionRenderer(XMLRenderer):

    def render_document(self, xml, questions):
        xml.startElement('rdmo', {
            'xmlns:dc': 'http://purl.org/dc/elements/1.1/'
        })
        for question in questions:
            self.render_question(xml, question)
        xml.endElement('rdmo')
