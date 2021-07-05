from rdmo.core.renderers import BaseXMLRenderer


class XMLRenderer(BaseXMLRenderer):

    def render_document(self, xml, project):
        xml.startElement('project', {
            'xmlns:dc': 'http://purl.org/dc/elements/1.1/'
        })
        self.render_text_element(xml, 'title', {}, project['title'])
        self.render_text_element(xml, 'description', {}, project['description'])
        self.render_text_element(xml, 'catalog', {'dc:uri': project['catalog']}, None)

        if 'tasks' in project and project['tasks']:
            xml.startElement('tasks', {})
            for task in project['tasks']:
                self.render_text_element(xml, 'task', {'dc:uri': task}, None)
            xml.endElement('tasks')

        if 'views' in project and project['views']:
            xml.startElement('views', {})
            for view in project['views']:
                self.render_text_element(xml, 'view', {'dc:uri': view}, None)
            xml.endElement('views')

        if 'snapshots' in project and project['snapshots']:
            xml.startElement('snapshots', {})
            for snapshot in project['snapshots']:
                self.render_snapshot(xml, snapshot)
            xml.endElement('snapshots')

        if 'values' in project and project['values']:
            xml.startElement('values', {})
            for value in project['values']:
                self.render_value(xml, value)
            xml.endElement('values')

        self.render_text_element(xml, 'created', {}, project['created'])
        self.render_text_element(xml, 'updated', {}, project['updated'])
        xml.endElement('project')

    def render_snapshot(self, xml, snapshot):
        xml.startElement('snapshot', {})
        self.render_text_element(xml, 'title', {}, snapshot['title'])
        self.render_text_element(xml, 'description', {}, snapshot['description'])

        if 'values' in snapshot and snapshot['values']:
            xml.startElement('values', {})
            for value in snapshot['values']:
                self.render_value(xml, value)
            xml.endElement('values')

        self.render_text_element(xml, 'created', {}, snapshot['created'])
        self.render_text_element(xml, 'updated', {}, snapshot['updated'])
        xml.endElement('snapshot')

    def render_value(self, xml, value):
        xml.startElement('value', {})
        self.render_text_element(xml, 'attribute', {'dc:uri': value['attribute']}, None)
        self.render_text_element(xml, 'set_prefix', {}, value['set_prefix'])
        self.render_text_element(xml, 'set_index', {}, value['set_index'])
        self.render_text_element(xml, 'collection_index', {}, value['collection_index'])
        self.render_text_element(xml, 'text', {}, value['text'])
        self.render_text_element(xml, 'option', {'dc:uri': value['option']}, None)
        self.render_text_element(xml, 'file', {'name': value['file_name']}, value['file_content'])
        self.render_text_element(xml, 'value_type', {}, value['value_type'])
        self.render_text_element(xml, 'unit', {}, value['unit'])
        self.render_text_element(xml, 'external_id', {}, value['external_id'])
        self.render_text_element(xml, 'created', {}, value['created'])
        self.render_text_element(xml, 'updated', {}, value['updated'])
        xml.endElement('value')
