from django import template
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from ..utils import get_full_name

register = template.Library()


@register.simple_tag()
def full_name(user):
    return get_full_name(user)


@register.simple_tag()
def user_data_as_dl(user):
    html = '<dl>'
    html += '<dt>%(key)s</dt><dd>%(value)s</dd>' % {
        'key': _('Name'),
        'value': get_full_name(user)
    }
    for additional_value in user.additional_values.all():
        html += '<dt>%(key)s</dt><dd>%(value)s</dd>' % {
            'key': additional_value.field.text,
            'value': additional_value.value
        }
    html += '</dl>'
    return mark_safe(html)
