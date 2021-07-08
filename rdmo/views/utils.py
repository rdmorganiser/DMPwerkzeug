from django.utils.functional import cached_property
from mptt.utils import get_cached_trees

from rdmo.conditions.models import Condition
from collections import defaultdict


class ProjectWrapper(object):

    def __init__(self, project, snapshot=None):
        self._project = project
        self._snapshot = snapshot
        self._checked_conditions = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    def __str__(self):
        return str(self._project.title)

    @property
    def id(self):
        return self._project.id

    @property
    def title(self):
        return self._project.title

    @property
    def description(self):
        return self._project.description

    @property
    def created(self):
        return self._project.created

    @property
    def updated(self):
        return self._project.updated

    @property
    def snapshot(self):
        if self._snapshot:
            return {
                'id': self._snapshot.id,
                'title': self._snapshot.title,
                'description': self._snapshot.description,
                'created': self._snapshot.created,
                'updated': self._snapshot.updated
            }
        else:
            return {}

    @cached_property
    def descendants(self):
        return [ProjectWrapper(descendant) for descendant in self._project.get_descendants()]

    @cached_property
    def children(self):
        return [ProjectWrapper(child) for child in self._project.get_children()]

    @cached_property
    def tree(self):
        cached_trees = get_cached_trees(self._project.get_descendants())
        return self._build_tree(cached_trees)

    @cached_property
    def conditions(self):
        conditions = {}
        for condition in self._conditions:
            conditions[condition.uri] = conditions[condition.key] = self._check_condition(condition)
        return conditions

    @cached_property
    def _values(self):
        return list(self._project.values.filter(snapshot=self._snapshot).select_related('attribute', 'option'))

    @cached_property
    def _conditions(self):
        return list(Condition.objects.select_related('source', 'target_option').prefetch_related(
            'questions',
            'questionsets'
        ))

    def _check_conditions(self, conditions, set_prefix=None, set_index=None):
        # caches the result of the check in the wrapper
        if conditions:
            for condition in conditions:
                if self._check_condition(condition, set_prefix, set_index):
                    return True
            return False
        else:
            return True

    def _check_condition(self, condition, set_prefix=None, set_index=None):
        # caches the result of the check in the wrapper
        if self._checked_conditions[condition.id][set_prefix][set_index] == []:
            self._checked_conditions[condition.id][set_prefix][set_index] = \
                condition.resolve(self._values, set_prefix, set_index)

        return self._checked_conditions[condition.id][set_prefix][set_index]

    def _build_tree(self, projects):
        return [{
            'id': project.id,
            'level': project.level,
            'children': self.build_tree(project.get_children())
        } for project in projects]
