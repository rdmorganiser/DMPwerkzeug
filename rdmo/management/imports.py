from rdmo.conditions.imports import import_condition
from rdmo.core.constants import PERMISSIONS
from rdmo.domain.imports import fetch_attribute_parents, import_attribute
from rdmo.options.imports import (fetch_option_parents, import_option,
                                  import_optionset)
from rdmo.questions.imports import (fetch_question_parents,
                                    fetch_questionset_parents,
                                    fetch_section_parents, import_catalog,
                                    import_question, import_questionset,
                                    import_section)
from rdmo.tasks.imports import import_task
from rdmo.views.imports import import_view


def check_permissions(elements, user):
    element_types = set([element.get('type') for element in elements])

    permissions = []
    for element_type in element_types:
        permissions += PERMISSIONS[element_type]

    return user.has_perms(permissions)


def get_parent_uri(element_uri, parent_uri, parents, uris):
    if element_uri in parents and parents[element_uri]:
        # parent was explicitely selected
        return parents[element_uri]
    elif parent_uri in uris:
        # parent uri was changed during the import
        return uris[parent_uri]
    else:
        # needs to be False, to use parent uri in file
        return False


def import_elements(elements, parents={}, save={}):
    instances = []
    uris = {}

    for element in elements:
        element_type = element.get('type')
        save_element = save.get(element.get('uri'))

        # step 1: get create model for elements
        if element_type == 'condition':
            instance = import_condition(element, save=save_element)

        elif element_type == 'attribute':
            parent_uri = get_parent_uri(element.get('uri'), element.get('parent'), parents, uris)
            instance = import_attribute(element, parent_uri=parent_uri, save=save_element)

        elif element_type == 'optionset':
            instance = import_optionset(element, save=save_element)

        elif element_type == 'option':
            optionset_uri = get_parent_uri(element.get('uri'), element.get('optionset'), parents, uris)
            instance = import_option(element, optionset_uri=optionset_uri, save=save_element)

        elif element_type == 'catalog':
            instance = import_catalog(element, save=save_element)

        elif element_type == 'section':
            catalog_uri = get_parent_uri(element.get('uri'), element.get('catalog'), parents, uris)
            instance = import_section(element, catalog_uri=catalog_uri, save=save_element)

        elif element_type == 'questionset':
            section_uri = get_parent_uri(element.get('uri'), element.get('section'), parents, uris)
            questionset_uri = get_parent_uri(element.get('uri'), element.get('questionset'), {}, uris)
            instance = import_questionset(element, section_uri=section_uri, questionset_uri=questionset_uri, save=save_element)

        elif element_type == 'question':
            questionset_uri = get_parent_uri(element.get('uri'), element.get('questionset'), parents, uris)
            instance = import_question(element, questionset_uri=questionset_uri, save=save_element)

        elif element_type == 'task':
            instance = import_task(element, save=save_element)

        elif element_type == 'view':
            instance = import_view(element, save=save_element)

        else:
            instance = None

        # step 2: fetch available parents
        if instance:
            if not save:
                if element_type == 'attribute':
                    instance.parents = fetch_attribute_parents(instances)

                elif element.get('type') == 'option':
                    instance.parents = fetch_option_parents(instances)

                elif element.get('type') == 'section':
                    instance.parents = fetch_section_parents(instances)

                elif element.get('type') == 'questionset':
                    instance.parents = fetch_questionset_parents(instances)

                elif element.get('type') == 'question':
                    instance.parents = fetch_question_parents(instances)

                # check if a missing element was already imported
                for uri in instance.missing:
                    if uri in [instance.uri for instance in instances]:
                        instance.missing[uri]['in_file'] = True

            # append the instance to the list of instances
            instances.append(instance)

            if element.get('uri') != instance.uri:
                uris[element.get('uri')] = instance.uri

    return instances
