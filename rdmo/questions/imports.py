import logging

from django.contrib.sites.models import Site

from rdmo.conditions.models import Condition
from rdmo.core.imports import (fetch_parents, get_foreign_field,
                               get_m2m_instances, set_common_fields,
                               set_lang_field, validate_instance)
from rdmo.domain.models import Attribute
from rdmo.options.models import Option, OptionSet

from .models import Catalog, Question, QuestionSet, Section
from .validators import (CatalogLockedValidator, CatalogUniqueURIValidator,
                         QuestionLockedValidator, QuestionSetLockedValidator,
                         QuestionSetUniqueURIValidator,
                         QuestionUniqueURIValidator, SectionLockedValidator,
                         SectionUniqueURIValidator)

logger = logging.getLogger(__name__)


def import_catalog(element, save=False):
    try:
        catalog = Catalog.objects.get(uri=element.get('uri'))
    except Catalog.DoesNotExist:
        catalog = Catalog()

    set_common_fields(catalog, element)

    catalog.order = element.get('order') or 0

    set_lang_field(catalog, 'title', element)

    if save and validate_instance(catalog, CatalogLockedValidator, CatalogUniqueURIValidator):
        if catalog.id:
            logger.info('Catalog created with uri %s.', element.get('uri'))
        else:
            logger.info('Catalog %s updated.', element.get('uri'))

        catalog.save()
        catalog.sites.add(Site.objects.get_current())
        catalog.imported = True

    return catalog


def import_section(element, parent_uri=False, save=False):
    if parent_uri is False:
        parent_uri = element.get('catalog')

    try:
        section = Section.objects.get(uri=element.get('uri'), catalog__uri=parent_uri)
    except Section.DoesNotExist:
        section = Section()

    set_common_fields(section, element)

    section.parent_uri = parent_uri
    section.catalog = get_foreign_field(section, parent_uri, Catalog)

    section.order = element.get('order') or 0

    set_lang_field(section, 'title', element)

    if save and validate_instance(section, SectionLockedValidator, SectionUniqueURIValidator):
        if section.id:
            logger.info('Section created with uri %s.', element.get('uri'))
        else:
            logger.info('Section %s updated.', element.get('uri'))

        section.save()
        section.imported = True

    return section


def import_questionset(element, parent_uri=False, save=False):
    if parent_uri is False:
        parent_uri = element.get('section')

    try:
        questionset = QuestionSet.objects.get(uri=element.get('uri'), section__uri=parent_uri)
    except QuestionSet.DoesNotExist:
        questionset = QuestionSet()

    set_common_fields(questionset, element)

    questionset.parent_uri = parent_uri
    questionset.section = get_foreign_field(questionset, parent_uri, Section)
    questionset.questionset = get_foreign_field(questionset, element.get('questionset'), QuestionSet)
    questionset.attribute = get_foreign_field(questionset, element.get('attribute'), Attribute)
    questionset.is_collection = element.get('is_collection') or False
    questionset.order = element.get('order') or 0

    set_lang_field(questionset, 'title', element)
    set_lang_field(questionset, 'help', element)
    set_lang_field(questionset, 'verbose_name', element)
    set_lang_field(questionset, 'verbose_name_plural', element)

    conditions = get_m2m_instances(questionset, element.get('conditions'), Condition)

    if save and validate_instance(questionset, QuestionSetLockedValidator, QuestionSetUniqueURIValidator):
        if questionset.id:
            logger.info('QuestionSet created with uri %s.', element.get('uri'))
        else:
            logger.info('QuestionSet %s updated.', element.get('uri'))

        questionset.save()
        questionset.conditions.set(conditions)
        questionset.imported = True

    return questionset


def import_question(element, parent_uri=False, save=False):
    if parent_uri is False:
        parent_uri = element.get('questionset')

    try:
        question = Question.objects.get(uri=element.get('uri'), questionset__uri=parent_uri)
    except Question.DoesNotExist:
        question = Question()

    set_common_fields(question, element)

    question.parent_uri = parent_uri
    question.questionset = get_foreign_field(question, parent_uri, QuestionSet)

    question.attribute = get_foreign_field(question, element.get('attribute'), Attribute)
    question.is_collection = element.get('is_collection') or False
    question.is_optional = element.get('is_optional') or False
    question.order = element.get('order') or 0

    set_lang_field(question, 'text', element)
    set_lang_field(question, 'help', element)
    set_lang_field(question, 'default_text', element)
    set_lang_field(question, 'verbose_name', element)
    set_lang_field(question, 'verbose_name_plural', element)

    question.default_option = get_foreign_field(question, element.get('default_option'), Option)
    question.default_external_id = element.get('default_external_id') or ''

    question.widget_type = element.get('widget_type') or ''
    question.value_type = element.get('value_type') or ''
    question.maximum = element.get('maximum')
    question.minimum = element.get('minimum')
    question.step = element.get('step')
    question.unit = element.get('unit') or ''
    question.width = element.get('width')

    conditions = get_m2m_instances(question, element.get('conditions'), Condition)
    optionsets = get_m2m_instances(question, element.get('optionsets'), OptionSet)

    if save and validate_instance(question, QuestionLockedValidator, QuestionUniqueURIValidator):
        if question.id:
            logger.info('Question created with uri %s.', element.get('uri'))
        else:
            logger.info('Question %s updated.', element.get('uri'))

        question.save()
        question.conditions.set(conditions)
        question.optionsets.set(optionsets)
        question.imported = True

    return question


def fetch_section_parents(instances):
    return fetch_parents(Catalog, instances)


def fetch_questionset_parents(instances):
    return fetch_parents(Section, instances)


def fetch_question_parents(instances):
    return fetch_parents(QuestionSet, instances)
