from collections import defaultdict

from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext_lazy as _

from rdmo.core.imports import handle_uploaded_file
from rdmo.core.plugins import get_plugin, get_plugins
from rdmo.questions.models import Question

from .models import Membership, Project
from .utils import (save_import_snapshot_values, save_import_tasks,
                    save_import_values, save_import_views)


class ProjectImportMixin(object):

    def get_current_values(self, current_project):
        queryset = current_project.values.filter(snapshot=None).select_related('attribute', 'option')

        current_values = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
        for value in queryset:
            current_values[value.attribute.uri][value.set_prefix][value.set_index][value.collection_index] = value
        return current_values

    def get_questions(self, catalog):
        queryset = Question.objects.filter(questionset__section__catalog=catalog) \
                                   .select_related('attribute') \
                                   .order_by('attribute__uri')

        questions = {}
        for question in queryset:
            if question.attribute.uri not in questions:
                questions[question.attribute.uri] = question
        return questions

    def update_values(self, current_project, catalog, values, snapshots=[]):
        questions = self.get_questions(catalog)
        current_values = self.get_current_values(current_project) if current_project else {}

        for value in values:
            if value.attribute:
                value.pk = None
                value.question = questions.get(value.attribute.uri)
                value.current = current_values.get(value.attribute.uri, {}) \
                                              .get(value.set_prefix, {}) \
                                              .get(value.set_index, {}) \
                                              .get(value.collection_index)

        for snapshot in snapshots:
            snapshot.pk = None

            for value in snapshot.snapshot_values:
                if value.attribute:
                    value.pk = None
                    value.question = questions.get(value.attribute.uri)
                    value.current = current_values.get(value.attribute.uri, {}) \
                                                  .get(value.set_prefix, {}) \
                                                  .get(value.set_index, {}) \
                                                  .get(value.collection_index)

    def upload_file(self):
        current_project = self.object

        try:
            uploaded_file = self.request.FILES['uploaded_file']
        except KeyError:
            return None
        else:
            import_tmpfile_name = handle_uploaded_file(uploaded_file)

        for import_key, import_plugin in get_plugins('PROJECT_IMPORTS').items():
            import_plugin.file_name = import_tmpfile_name
            import_plugin.current_project = current_project

            if import_plugin.check():
                try:
                    import_plugin.process()
                except ValidationError as e:
                    return render(self.request, 'core/error.html', {
                        'title': _('Import error'),
                        'errors': e
                    }, status=400)

                # store information in session for ProjectCreateImportView
                self.request.session['update_import_tmpfile_name'] = import_tmpfile_name
                self.request.session['update_import_key'] = import_key

                # attach questions and current values
                self.update_values(current_project, import_plugin.catalog, import_plugin.values, import_plugin.snapshots)

                return render(self.request, 'projects/project_import.html', {
                    'method': 'import_file',
                    'current_project': current_project,
                    'source_title': uploaded_file.name,
                    'source_project': import_plugin.project,
                    'values': import_plugin.values,
                    'snapshots': import_plugin.snapshots if current_project else None,
                    'tasks': import_plugin.tasks,
                    'views': import_plugin.views
                })

        return render(self.request, 'core/error.html', {
            'title': _('Import error'),
            'errors': [_('Files of this type cannot be imported.')]
        }, status=400)

    def import_file(self):
        current_project = self.object

        import_tmpfile_name = self.request.session.get('update_import_tmpfile_name')
        import_key = self.request.session.get('update_import_key')
        checked = [key for key, value in self.request.POST.items() if 'on' in value]

        if import_tmpfile_name and import_key:
            import_plugin = get_plugin('PROJECT_IMPORTS', import_key)
            import_plugin.file_name = import_tmpfile_name
            import_plugin.current_project = current_project

            if import_plugin.check():
                try:
                    import_plugin.process()
                except ValidationError as e:
                    return render(self.request, 'core/error.html', {
                        'title': _('Import error'),
                        'errors': e
                    }, status=400)

                # attach questions and current values
                self.update_values(current_project, import_plugin.catalog, import_plugin.values, import_plugin.snapshots)

                if current_project:
                    save_import_values(self.object, import_plugin.values, checked)
                    save_import_tasks(self.object, import_plugin.tasks)
                    save_import_views(self.object, import_plugin.views)

                    return HttpResponseRedirect(current_project.get_absolute_url())

                else:
                    # add current site and save project
                    import_plugin.project.site = get_current_site(self.request)
                    import_plugin.project.save()

                    # add user to project
                    membership = Membership(project=import_plugin.project, user=self.request.user, role='owner')
                    membership.save()

                    for value in import_plugin.values:
                        value.current = None

                    save_import_values(import_plugin.project, import_plugin.values, checked)
                    save_import_snapshot_values(import_plugin.project, import_plugin.snapshots, checked)
                    save_import_tasks(import_plugin.project, import_plugin.tasks)
                    save_import_views(import_plugin.project, import_plugin.views)

                    return HttpResponseRedirect(import_plugin.project.get_absolute_url())

    def import_project(self):
        current_project = self.object

        # get the original project
        project = get_object_or_404(Project.objects.all(), id=self.request.POST.get('source'))

        # check if the user has the permission to access the original project
        if not self.request.user.has_perm('projects.view_project_object', project):
            self.handle_no_permission()

        values = project.values.filter(snapshot=None) \
                               .select_related('attribute', 'option')

        # attach questions and current values
        self.update_values(current_project, current_project.catalog, values)

        checked = [key for key, value in self.request.POST.items() if 'on' in value]
        if checked:
            save_import_values(current_project, values, checked)
            return HttpResponseRedirect(current_project.get_absolute_url())

        else:
            return render(self.request, 'projects/project_import.html', {
                'method': 'import_project',
                'source': project.id,
                'source_title': project.title,
                'current_project': current_project,
                'values': values,
            })
