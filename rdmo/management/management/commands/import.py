import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _

from rdmo.core.xml import flat_xml_to_elements, read_xml_file
from rdmo.management.imports import import_elements

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('xmlfile', action='store', default=False, help='RDMO XML export file')

    def handle(self, *args, **options):
        root = read_xml_file(options['xmlfile'])
        if root is None:
            raise CommandError(_('The content of the xml file does not consist of well formed data or markup.'))
        elif root.tag != 'rdmo':
            raise CommandError(_('This XML does not contain RDMO content.'))
        else:
            elements = flat_xml_to_elements(root)
            save = {element.get('uri'): True for element in elements}
            import_elements(elements, save=save)
