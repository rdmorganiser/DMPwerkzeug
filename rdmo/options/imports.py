import logging

from rdmo.conditions.models import Condition
from rdmo.core.imports import (fetch_parents, get_foreign_field,
                               get_m2m_instances, set_common_fields,
                               set_lang_field, validate_instance)

from .models import Option, OptionSet
from .validators import (OptionLockedValidator, OptionSetLockedValidator,
                         OptionSetUniqueURIValidator, OptionUniqueURIValidator)

logger = logging.getLogger(__name__)


def import_optionset(element, save=False):
    try:
        optionset = OptionSet.objects.get(uri=element.get('uri'))
    except OptionSet.DoesNotExist:
        optionset = OptionSet()

    set_common_fields(optionset, element)

    optionset.order = element.get('order') or 0
    optionset.provider_key = element.get('provider_key') or ''

    conditions = get_m2m_instances(optionset, element.get('conditions'), Condition)

    if save and validate_instance(optionset, OptionSetLockedValidator, OptionSetUniqueURIValidator):
        if optionset.id:
            logger.info('OptionSet created with uri %s.', element.get('uri'))
        else:
            logger.info('OptionSet %s updated.', element.get('uri'))

        optionset.save()
        optionset.conditions.set(conditions)
        optionset.imported = True

    return optionset


def import_option(element, parent_uri=False, save=False):
    if parent_uri is False:
        parent_uri = element.get('optionset')

    try:
        option = Option.objects.get(uri=element.get('uri'), optionset__uri=parent_uri)
    except Option.DoesNotExist:
        option = Option()

    set_common_fields(option, element)

    option.parent_uri = parent_uri
    option.optionset = get_foreign_field(option, parent_uri, OptionSet)

    option.order = element.get('order') or 0
    option.additional_input = element.get('additional_input') or False

    set_lang_field(option, 'text', element)

    if save and validate_instance(option, OptionLockedValidator, OptionUniqueURIValidator):
        if option.id:
            logger.info('Option created with uri %s.', element.get('uri'))
        else:
            logger.info('Option %s updated.', element.get('uri'))

        option.save()
        option.imported = True

    return option


def fetch_option_parents(instances):
    return fetch_parents(OptionSet, instances)
