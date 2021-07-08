import base64
import io
import logging
import mimetypes

from django.core.files import File

from rdmo.core.plugins import Plugin
from rdmo.core.xml import get_ns_map, get_uri, read_xml_file
from rdmo.domain.models import Attribute
from rdmo.options.models import Option
from rdmo.questions.models import Catalog
from rdmo.tasks.models import Task
from rdmo.views.models import View

from .models import Project, Snapshot, Value

log = logging.getLogger(__name__)


class Import(Plugin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.file_name = None
        self.current_project = None
        self.project = None
        self.catalog = None

        self._attributes = {attribute.uri: attribute for attribute in Attribute.objects.all()}
        self._options = {option.uri: option for option in Option.objects.all()}
        self._tasks = {task.uri: task for task in Task.objects.all()}
        self._views = {view.uri: view for view in View.objects.all()}

        self.values = []
        self.snapshots = []
        self.tasks = []
        self.views = []

    def check(self):
        raise NotImplementedError

    def process(self):
        raise NotImplementedError

    def get_attribute(self, attribute_uri):
        try:
            return self._attributes.get(attribute_uri)
        except KeyError:
            log.info('Attribute %s not in db. Skipping.', attribute_uri)

    def get_option(self, option_uri):
        try:
            return self._options.get(option_uri)
        except KeyError:
            log.info('Option %s not in db. Skipping.', option_uri)

    def get_task(self, tasks_uri):
        try:
            return self._tasks.get(tasks_uri)
        except KeyError:
            log.info('Task %s not in db. Skipping.', tasks_uri)

    def get_view(self, view_uri):
        try:
            return self._views.get(view_uri)
        except KeyError:
            log.info('View %s not in db. Skipping.', view_uri)


class RDMOXMLImport(Import):

    def check(self):
        file_type, encoding = mimetypes.guess_type(self.file_name)
        if file_type == 'application/xml' or file_type == 'text/xml':
            self.root = read_xml_file(self.file_name)
            if self.root and self.root.tag == 'project':
                self.ns_map = get_ns_map(self.root)
                return True

    def process(self):
        if self.current_project is None:
            catalog_uri = get_uri(self.root.find('catalog'), self.ns_map)
            try:
                self.catalog = Catalog.objects.all().get(uri=catalog_uri)
            except Catalog.DoesNotExist:
                log.info('Catalog not in db. Created with uri %s', catalog_uri)
                self.catalog = Catalog.objects.all().first()

            self.project = Project()
            self.project.title = self.root.find('title').text or ''
            self.project.description = self.root.find('description').text or ''
            self.project.created = self.root.find('created').text
            self.project.catalog = self.catalog
        else:
            self.catalog = self.current_project.catalog

        tasks_node = self.root.find('tasks')
        if tasks_node is not None:
            for task_node in tasks_node.findall('task'):
                task_uri = get_uri(task_node, self.ns_map)
                if task_uri:
                    task = self.get_task(task_uri)
                    if task:
                        self.tasks.append(task)

        views_node = self.root.find('views')
        if views_node is not None:
            for view_node in views_node.findall('view'):
                view_uri = get_uri(view_node, self.ns_map)
                if view_uri:
                    view = self.get_view(view_uri)
                    if view:
                        self.views.append(view)

        values_node = self.root.find('values')
        if values_node is not None:
            for value_node in values_node.findall('value'):
                self.values.append(self.get_value(value_node))

        snapshots_node = self.root.find('snapshots')
        if snapshots_node is not None:
            for snapshot_index, snapshot_node in enumerate(snapshots_node.findall('snapshot')):
                if snapshot_node is not None:
                    snapshot = Snapshot()
                    snapshot.title = snapshot_node.find('title').text or ''
                    snapshot.description = snapshot_node.find('description').text or ''
                    snapshot.created = snapshot_node.find('created').text

                    snapshot_values = []
                    snapshot_values_node = snapshot_node.find('values')
                    if snapshot_values_node is not None:
                        for snapshot_value_node in snapshot_values_node.findall('value'):
                            snapshot_values.append(self.get_value(snapshot_value_node))

                    snapshot.snapshot_index = snapshot_index
                    snapshot.snapshot_values = snapshot_values

                    self.snapshots.append(snapshot)

    def get_value(self, value_node):
        value = Value()

        attribute_uri = get_uri(value_node.find('attribute'), self.ns_map)
        if attribute_uri is not None:
            value.attribute = self.get_attribute(attribute_uri)

        value.set_prefix = ''
        try:
            value.set_prefix = value_node.find('set_prefix').text
        except AttributeError:
            pass
        value.set_index = int(value_node.find('set_index').text)
        value.collection_index = int(value_node.find('collection_index').text)
        value.text = value_node.find('text').text or ''

        option_uri = get_uri(value_node.find('option'), self.ns_map)
        if option_uri:
            value.option = self.get_option(option_uri)

        value.file_import = None
        file_node = value_node.find('file')
        if file_node is not None:
            file_string = file_node.text
            if file_string is not None:
                value.file_import = {
                    'name': file_node.attrib.get('name', 'file.dat'),
                    'file': File(io.BytesIO(base64.b64decode(file_string)))
                }

        value_type_node = value_node.find('value_type')
        if value_type_node is not None:
            value.value_type = value_type_node.text or ''

        unit_node = value_node.find('unit')
        if unit_node is not None:
            value.unit = unit_node.text or ''

        external_id_node = value_node.find('external_id')
        if external_id_node is not None:
            value.external_id = external_id_node.text or ''

        value.created = value_node.find('created').text
        value.updated = value_node.find('updated').text

        return value
