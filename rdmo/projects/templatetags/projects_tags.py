from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from rdmo.views.templatetags.view_tags import get_value

from ..models import Membership

register = template.Library()


@register.simple_tag()
def projects_indent(level):
    string = ''
    if level > 0:
        for _ in range(level - 1):
            string += '&ensp;&ensp;'
        string += '&#8226;&ensp;'

    return mark_safe('<span class="projects-indent">' + string + '</span>')


@register.filter()
@stringfilter
def projects_role(role):
    return dict(Membership.ROLE_CHOICES).get(role, '')


@register.simple_tag(takes_context=True)
def get_labels(context, question, set_prefix='', set_index=0, project=None):
    if question.questionset.is_collection:
        set_labels = []

        for questionset in question.questionset.get_ancestors(ascending=True, include_self=True):
            set_label = '#{}'.format(set_index + 1)

            if questionset.attribute:
                # get attribute value
                value = get_value(context, questionset.attribute.uri, set_prefix=set_prefix, set_index=set_index, index=0, project=project)
                if value:
                    set_label = '"{}"'.format(value['value'])

            set_labels.append('{} {}'.format(questionset.verbose_name.title() or _('Set'), set_label))

            if set_prefix != '':
                rpartition = set_prefix.rpartition('|')
                set_prefix, set_index = rpartition[0], int(rpartition[2])

        # flip the list
        set_labels.reverse()

        return set_labels
    else:
        return None


@register.simple_tag(takes_context=True)
def check_question(context, question, set_prefix=None, set_index=None, project=None):
    if project is None:
        project = context['project']

    conditions = list(filter(lambda condition: question in condition.questions.all(), project._conditions))
    return project._check_conditions(conditions, set_prefix=set_prefix, set_index=set_index)


@register.simple_tag(takes_context=True)
def check_questionset(context, questionset, set_prefix=None, set_index=None, project=None):
    if project is None:
        project = context['project']

    conditions = list(filter(lambda condition: questionset in condition.questionsets.all(), project._conditions))
    return project._check_conditions(conditions, set_prefix=set_prefix, set_index=set_index)
