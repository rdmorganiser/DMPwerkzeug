import logging
import tempfile
import time
from os.path import join as pj
from random import randint

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from rdmo.core.utils import get_languages

logger = logging.getLogger(__name__)


def handle_uploaded_file(filedata):
    tempfilename = generate_tempfile_name()
    with open(tempfilename, 'wb+') as destination:
        for chunk in filedata.chunks():
            destination.write(chunk)
    return tempfilename


def generate_tempfile_name():
    t = int(round(time.time() * 1000))
    r = randint(10000, 99999)
    fn = pj(tempfile.gettempdir(), 'upload_' + str(t) + '_' + str(r) + '.xml')
    return fn


def set_common_fields(instance, element):
    instance.uri_prefix = element.get('uri_prefix') or ''
    instance.key = element.get('key') or ''
    instance.comment = element.get('comment') or ''

    # these are temporary fields for the import only
    # uri is set automatically when saving the instance
    instance.uri = element.get('uri')
    instance.object_name = instance._meta.object_name
    instance.missing = {}
    instance.errors = []


def set_lang_field(instance, field_name, element):
    for lang_code, lang_string, lang_field in get_languages():
        field = element.get('%s_%s' % (field_name, lang_code))
        if field:
            setattr(instance, '%s_%s' % (field_name, lang_field), field)


def get_foreign_field(instance, foreign_uri, foreign_model):
    if foreign_uri:
        try:
            return foreign_model.objects.get(uri=foreign_uri)
        except foreign_model.DoesNotExist:
            logger.info('{foreign_model} {foreign_uri} for {instance_model} {instance_uri} does not exist.'.format(
                foreign_model=foreign_model._meta.object_name,
                foreign_uri=foreign_uri,
                instance_model=instance._meta.object_name,
                instance_uri=instance.uri
            ))
            instance.missing[foreign_uri] = {
                'foreign_model': foreign_model._meta.verbose_name,
                'foreign_uri': foreign_uri
            }

    # return None by default
    return None


def get_m2m_instances(instance, foreign_uris, foreign_model):
    foreign_instances = []

    if foreign_uris:
        for foreign_uri in foreign_uris:
            try:
                foreign_instance = foreign_model.objects.get(uri=foreign_uri)
                foreign_instances.append(foreign_instance)
            except foreign_model.DoesNotExist:
                logger.info('{foreign_model} {foreign_uri} for imported {instance_model} {instance_uri} does not exist.'.format(
                    foreign_model=foreign_model._meta.object_name,
                    foreign_uri=foreign_uri,
                    instance_model=instance._meta.object_name,
                    instance_uri=instance.uri
                ))
                instance.missing[foreign_uri] = {
                    'foreign_model': foreign_model._meta.verbose_name,
                    'foreign_uri': foreign_uri
                }

    return foreign_instances


def validate_instance(instance, *validators):
    exception_message = None
    try:
        for validator in validators:
            data = vars(instance)

            # add foreign keys to parent fields to data
            for parent_field in getattr(instance, 'parent_fields', []):
                data[parent_field] = getattr(instance, parent_field, None)

            # run the validator
            validator(instance if instance.id else None)(data)

    except ValidationError as e:
        try:
            exception_message = '; '.join(['{}: {}'.format(key, ', '.join(messages)) for key, messages in e.message_dict.items()])
        except AttributeError:
            exception_message = ''.join(e.messages)
    except ObjectDoesNotExist as e:
        exception_message = e
    else:
        return True
    finally:
        if exception_message is not None:
            message = '{instance_model} {instance_uri} cannot be imported ({exception}).'.format(
                instance_model=instance._meta.object_name,
                instance_uri=instance.uri,
                exception=exception_message
            )
            logger.info(message)
            instance.errors.append(message)


def fetch_parents(model, instances):
    parents = list(model.objects.values_list('uri', flat=True))
    parents += [instance.uri for instance in instances if isinstance(instance, model)]
    return set(sorted(parents))
