from urllib.parse import urlparse

from django import template

from rdmo.core.constants import (VALUE_TYPE_DATETIME, VALUE_TYPE_INTEGER,
                                 VALUE_TYPE_TEXT)
from rdmo.projects.models import Value

register = template.Library()


@register.simple_tag(takes_context=True)
def get_values(context, attribute, set_index='*', index='*', project=None):
    if project is None:
        project = context['project']

    if attribute == 'project/id':
        return [Value(text=project.id, value_type=VALUE_TYPE_INTEGER).as_dict]
    elif attribute == 'project/title':
        return [Value(text=project.title, value_type=VALUE_TYPE_TEXT).as_dict]
    elif attribute == 'project/description':
        return [Value(text=project.description, value_type=VALUE_TYPE_TEXT).as_dict]
    elif attribute == 'project/created':
        return [Value(text=project.created, value_type=VALUE_TYPE_DATETIME).as_dict]
    elif attribute == 'project/updated':
        return [Value(text=project.updated, value_type=VALUE_TYPE_DATETIME).as_dict]
    else:
        values = project._values

        if urlparse(attribute).scheme:
            values = filter(lambda value: value.attribute and (value.attribute.uri == attribute), values)
        else:
            values = filter(lambda value: value.attribute and (value.attribute.path == attribute), values)

        if set_index != '*':
            values = filter(lambda value: value.set_index == set_index, values)

        if index != '*':
            values = filter(lambda value: value.collection_index == index, values)

        return list(map(lambda value: value.as_dict, values))


@register.simple_tag(takes_context=True)
def get_value(context, attribute, set_index=0, index=0, project=None):
    try:
        return get_values(context, attribute, set_index=set_index, index=index, project=project)[0]
    except IndexError:
        return None


@register.simple_tag(takes_context=True)
def get_set_values(context, set, attribute, index='*', project=None):
    return get_values(context, attribute, set_index=set.get('set_index'), index=index, project=project)


@register.simple_tag(takes_context=True)
def get_set_value(context, set, attribute, index=0, project=None):
    try:
        return get_values(context, attribute, set_index=set.get('set_index'), index=index, project=project)[0]
    except IndexError:
        return None


@register.simple_tag(takes_context=True)
def get_sets(context, attribute, project=None):
    return get_values(context, attribute.rstrip('/') + '/id', index=0, project=project)


@register.simple_tag(takes_context=True)
def get_set(context, attribute, project=None):
    # for backwards compatibility, identical to get_sets
    return get_sets(context, attribute, project=project)


@register.inclusion_tag('views/tags/value.html', takes_context=True)
def render_value(context, attribute, set_index=0, index=0, project=None):
    context['value'] = get_value(context, attribute, set_index=set_index, index=index, project=project)
    return context


@register.inclusion_tag('views/tags/value_list.html', takes_context=True)
def render_value_list(context, attribute, set_index=0, project=None):
    context['values'] = get_values(context, attribute, set_index=set_index, project=project)
    return context


@register.inclusion_tag('views/tags/value_inline_list.html', takes_context=True)
def render_value_inline_list(context, attribute, set_index=0, project=None):
    context['values'] = get_values(context, attribute, set_index=set_index, project=project)
    return context


@register.inclusion_tag('views/tags/value.html', takes_context=True)
def render_set_value(context, set, attribute, index=0, project=None):
    context['value'] = get_set_value(context, set, attribute, index=index, project=project)
    return context


@register.inclusion_tag('views/tags/value_list.html', takes_context=True)
def render_set_value_list(context, set, attribute, project=None):
    context['values'] = get_set_values(context, set, attribute, project=project)
    return context


@register.inclusion_tag('views/tags/value_inline_list.html', takes_context=True)
def render_set_value_inline_list(context, set, attribute, project=None):
    context['values'] = get_set_values(context, set, attribute, project=project)
    return context
