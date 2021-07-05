import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, TemplateView
from rdmo.core.views import RedirectViewMixin
from rdmo.questions.models import Catalog
from rdmo.tasks.models import Task
from rdmo.views.models import View

from ..forms import ProjectForm
from ..mixins import ProjectImportMixin
from ..models import Membership, Project

logger = logging.getLogger(__name__)


class ProjectCreateView(LoginRequiredMixin, RedirectViewMixin, CreateView):
    model = Project
    form_class = ProjectForm

    def get_form_kwargs(self):
        catalogs = Catalog.objects.filter_current_site() \
                                  .filter_group(self.request.user) \
                                  .filter_availability(self.request.user)
        projects = Project.objects.filter_user(self.request.user)

        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({
            'catalogs': catalogs,
            'projects': projects
        })
        return form_kwargs

    def form_valid(self, form):
        # add current site
        form.instance.site = get_current_site(self.request)

        # save the project
        response = super(ProjectCreateView, self).form_valid(form)

        # add all tasks to project
        tasks = Task.objects.filter_current_site() \
                            .filter_group(self.request.user) \
                            .filter_availability(self.request.user)
        for task in tasks:
            form.instance.tasks.add(task)

        # add all views to project
        views = View.objects.filter_current_site() \
                            .filter_catalog(self.object.catalog) \
                            .filter_group(self.request.user) \
                            .filter_availability(self.request.user)
        for view in views:
            form.instance.views.add(view)

        # add current user as owner
        membership = Membership(project=form.instance, user=self.request.user, role='owner')
        membership.save()

        return response


class ProjectCreateImportView(ProjectImportMixin, LoginRequiredMixin, TemplateView):
    success_url = reverse_lazy('projects')

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(self.success_url)

    def post(self, request, *args, **kwargs):
        self.object = None

        method = request.POST.get('method')
        if method in ['upload_file', 'import_file']:
            response = getattr(self, method)()
        else:
            response = None

        if response is None:
            return render(request, 'core/error.html', {
                'title': _('Import error'),
                'errors': [_('There has been an error with your import.')]
            }, status=400)
        else:
            return response
