from django.db.models import Q
from django.utils.functional import cached_property
from mptt.utils import get_cached_trees

from rdmo.questions.models import Question


class ProjectWrapper(object):

    def __init__(self, project, snapshot=None):
        self._project = project
        self._snapshot = snapshot

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
    def _values(self):
        return list(self._project.values.filter(snapshot=self._snapshot).select_related('attribute', 'option'))

    def _build_tree(self, projects):
        return [{
            'id': project.id,
            'level': project.level,
            'children': self.build_tree(project.get_children())
        } for project in projects]
