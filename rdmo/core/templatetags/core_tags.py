from markdown import markdown as markdown_function

from django import template
from django.conf import settings
from django.utils import translation
from django.template.loader import render_to_string
from django.template.defaultfilters import stringfilter
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from rdmo import __version__

register = template.Library()


@register.simple_tag()
def i18n_switcher():
    string = ''
    for language, language_string in settings.LANGUAGES:
        url = reverse('i18n_switcher', args=[language])
        if language == translation.get_language():
            string += "<a class=\"dropdown-item\" href=\"%s\"><u>%s</u></a>" % (url, language_string)
        else:
            string += "<a class=\"dropdown-item\" href=\"%s\">%s</a>" % (url, language_string)

    return mark_safe(string)


@register.simple_tag()
@stringfilter
def vendor(vendor_key):
    vendor_config = settings.VENDOR[vendor_key]

    tags = []

    if 'js' in vendor_config:
        for file in vendor_config['js']:
            if settings.VENDOR_CDN:
                tag = '<script src="%(url)s/%(path)s" integrity="%(sri)s" crossorigin="anonymous"></script>' % {
                    'url': vendor_config['url'],
                    'path': file['path'],
                    'sri': file['sri'] if 'sri' in file else ''
                }
            else:
                tag = '<script src="%(static_url)s/%(vendor_key)s/%(path)s"></script>' % {
                    'static_url': settings.STATIC_URL.rstrip('/'),
                    'vendor_key': vendor_key,
                    'path': file['path']
                }

            tags.append(tag)


    if 'css' in vendor_config:
        for file in vendor_config['css']:
            if settings.VENDOR_CDN:
                tag = '<link rel="stylesheet" href="%(url)s/%(path)s" integrity="%(sri)s" crossorigin="anonymous" />' % {
                    'url': vendor_config['url'],
                    'path': file['path'],
                    'sri': file['sri'] if 'sri' in file else ''
                }
            else:
                tag = '<link rel="stylesheet" href="%(static_url)s/%(vendor_key)s/%(path)s" />' % {
                    'static_url': settings.STATIC_URL.rstrip('/'),
                    'vendor_key': vendor_key,
                    'path': file['path']
                }

            tags.append(tag)

    return mark_safe(''.join(tags))


@register.simple_tag(takes_context=True)
def bootstrap_form(context, **kwargs):
    form_context = {}

    if 'form' in kwargs:
        form_context['form'] = kwargs['form']
    else:
        form_context['form'] = context['form']

    if 'next' in kwargs:
        form_context['next'] = kwargs['next']
    elif 'next' in context:
        form_context['next'] = context['next']

    if 'action_url_name' in kwargs:
        form_context['action'] = reverse(kwargs['action_url_name'])

    if 'submit' in kwargs:
        form_context['submit'] = kwargs['submit']

    return render_to_string('core/bootstrap_form.html', form_context, request=context.request)


@register.simple_tag(takes_context=True)
def bootstrap_delete_form(context, **kwargs):
    form_context = {}

    if 'next' in kwargs:
        form_context['next'] = kwargs['next']
    elif 'next' in context:
        form_context['next'] = context['next']

    if 'action_url_name' in kwargs:
        form_context['action'] = reverse(kwargs['action_url_name'])

    if 'submit' in kwargs:
        form_context['submit'] = kwargs['submit']

    return render_to_string('core/bootstrap_delete_form.html', form_context, request=context.request)


@register.filter(name='next')
def next(value, arg):
    try:
        return value[int(arg)+1]
    except:
        return None


@register.filter(is_safe=True)
@stringfilter
def markdown(value):
    return mark_safe(markdown_function(force_text(value)))


@register.simple_tag
def version():
    return __version__
