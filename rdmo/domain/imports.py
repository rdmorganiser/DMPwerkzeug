import logging

from rdmo.core.imports import (fetch_parents, get_foreign_field,
                               set_common_fields, validate_instance)

from .models import Attribute
from .validators import (AttributeLockedValidator, AttributeParentValidator,
                         AttributeUniqueURIValidator)

logger = logging.getLogger(__name__)


def import_attribute(element, parent_uri=False, save=False):
    try:
        if parent_uri is False:
            attribute = Attribute.objects.get(uri=element.get('uri'))
        else:
            attribute = Attribute.objects.get(key=element.get('key'), parent__uri=parent_uri)
    except Attribute.DoesNotExist:
        attribute = Attribute()

    set_common_fields(attribute, element)

    attribute.parent = get_foreign_field(attribute, parent_uri or element.get('parent'), Attribute)

    if save and validate_instance(attribute,
                                  AttributeLockedValidator,
                                  AttributeParentValidator,
                                  AttributeUniqueURIValidator):
        if attribute.id:
            logger.debug('Attribute created with uri %s.', element.get('uri'))
        else:
            logger.debug('Attribute %s updated.', element.get('uri'))

        attribute.save()
        attribute.imported = True

    return attribute


def fetch_attribute_parents(instances):
    return fetch_parents(Attribute, instances)
