import logging
from urllib.parse import urlparse

import requests
from django import template

from rdmo.core.constants import VALUE_TYPE_DATETIME, VALUE_TYPE_TEXT

register = template.Library()
log = logging.getLogger(__name__)


@register.simple_tag(takes_context=True)
def get_project_title(context):
    title = context['project'].title
    value_model = context['project'].values.model
    return value_model(text=title, value_type=VALUE_TYPE_TEXT)


@register.simple_tag(takes_context=True)
def get_project_description(context):
    description = context['project'].description
    value_model = context['project'].values.model
    return value_model(text=description, value_type=VALUE_TYPE_TEXT)


@register.simple_tag(takes_context=True)
def get_project_created(context):
    created = context['project'].created
    value_model = context['project'].values.model
    return value_model(text=created, value_type=VALUE_TYPE_DATETIME)


@register.simple_tag(takes_context=True)
def get_project_updated(context):
    updated = context['project'].updated
    value_model = context['project'].values.model
    return value_model(text=updated, value_type=VALUE_TYPE_DATETIME)


@register.simple_tag(takes_context=True)
def get_values(context, attribute, set_index='*', index='*'):
    if attribute == 'project/title':
        return [get_project_title(context)]
    if attribute == 'project/description':
        return [get_project_description(context)]
    if attribute == 'project/created':
        return [get_project_created(context)]
    if attribute == 'project/updated':
        return [get_project_updated(context)]
    else:
        queryset = context['project'].values.filter(snapshot=context['current_snapshot'])

        if urlparse(attribute).scheme:
            queryset = queryset.filter(attribute__uri=attribute)
        else:
            queryset = queryset.filter(attribute__path=attribute)

        if set_index != '*':
            queryset = queryset.filter(set_index=set_index)

        if index != '*':
            queryset = queryset.filter(collection_index=index)

        return queryset.order_by('set_index').order_by('collection_index')


@register.simple_tag(takes_context=True)
def get_value(context, attribute, set_index=0, index=0):
    try:
        return get_values(context, attribute, set_index, index)[0]
    except IndexError:
        return None


@register.simple_tag(takes_context=True)
def get_set_values(context, set, attribute, index='*'):
    return get_values(context, attribute, set.set_index, index)


@register.simple_tag(takes_context=True)
def get_set_value(context, set, attribute, index=0):
    try:
        return get_values(context, attribute, set.set_index, index)[0]
    except IndexError:
        return None


@register.simple_tag(takes_context=True)
def get_sets(context, attribute):
    return get_values(context, attribute.rstrip('/') + '/id', index=0)


@register.simple_tag(takes_context=True)
def get_set(context, attribute):
    # for backwards compatibility, identical to get_sets
    return get_sets(context, attribute)


@register.inclusion_tag('views/tags/value.html', takes_context=True)
def render_value(context, attribute, set_index=0, index=0):
    return {'value': get_value(context, attribute, set_index, index)}


@register.inclusion_tag('views/tags/value_list.html', takes_context=True)
def render_value_list(context, attribute, set_index=0):
    return {'values': get_values(context, attribute, set_index)}


@register.inclusion_tag('views/tags/value_inline_list.html', takes_context=True)
def render_value_inline_list(context, attribute, set_index=0):
    return {'values': get_values(context, attribute, set_index)}


@register.inclusion_tag('views/tags/value.html', takes_context=True)
def render_set_value(context, set, attribute, index=0):
    return {'value': get_set_value(context, set, attribute, index)}


@register.inclusion_tag('views/tags/value_list.html', takes_context=True)
def render_set_value_list(context, set, attribute):
    return {'values': get_set_values(context, set, attribute)}


@register.inclusion_tag('views/tags/value_inline_list.html', takes_context=True)
def render_set_value_inline_list(context, set, attribute):
    return {'values': get_set_values(context, set, attribute)}


@register.simple_tag(takes_context=True)
def httpget(context, url):
    r = requests.get(url, auth=('user', 'pass'))
    if r.status_code == 200:
        return r.text
    else:
        log.error("View httpget failed %s, %s", url, r.status_code)
    return ''
