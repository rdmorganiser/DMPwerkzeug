from django.test import TestCase
from django.utils import translation

from apps.core.test_mixins import *

from .models import Project


class ProjectsTestCase(TestCase):
    fixtures = [
        'testing/accounts.json',
        'testing/domain.json',
        'testing/questions.json',
        'testing/projects.json'
    ]


class ProjectTests(TestModelViewMixin, TestModelStringMixin, ProjectsTestCase):

    list_url_name = 'projects'
    retrieve_url_name = 'project'

    create_url_name = 'project_create'
    update_url_name = 'project_update'
    delete_url_name = 'project_delete'

    api_url_name = 'projects:project'

    def setUp(self):
        translation.activate('en')
        self.client.login(username='user', password='user')
        self.instance = Project.objects.get(owner__username='user')

    def test_model_owner_string(self):
        self.assertIsNotNone(self.instance.owner_string())


class SnapshotTests(TestModelStringMixin, ProjectsTestCase):

    def setUp(self):
        translation.activate('en')
        self.client.login(username='user', password='user')
        self.instance = Project.objects.get(owner__username='user').current_snapshot
