import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import F, OuterRef, Subquery
from django.forms import Form
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import DeleteView, DetailView, TemplateView
from django.views.generic.edit import FormMixin
from django_filters.views import FilterView

from rdmo.accounts.utils import is_site_manager
from rdmo.core.plugins import get_plugin, get_plugins
from rdmo.core.views import ObjectPermissionMixin, RedirectViewMixin
from rdmo.questions.models import Catalog

from ..filters import ProjectFilter
from ..models import Integration, Invite, Membership, Project, Value

logger = logging.getLogger(__name__)


class ProjectsView(LoginRequiredMixin, FilterView):
    template_name = 'projects/projects.html'
    context_object_name = 'projects'
    paginate_by = 20
    filterset_class = ProjectFilter

    def get_queryset(self):
        # prepare projects queryset for this user
        queryset = Project.objects.filter(user=self.request.user)
        for instance in queryset:
            queryset |= instance.get_descendants()
        queryset = queryset.distinct()

        # prepare subquery for role
        membership_subquery = models.Subquery(
            Membership.objects.filter(project=models.OuterRef('pk'), user=self.request.user).values('role')
        )
        queryset = queryset.annotate(role=membership_subquery)

        # prepare subquery for last_changed
        last_changed_subquery = models.Subquery(
            Value.objects.filter(project=models.OuterRef('pk')).order_by('-updated').values('updated')[:1]
        )
        queryset = queryset.annotate(last_changed=models.functions.Greatest('updated', last_changed_subquery))

        # order by last changed
        queryset = queryset.order_by('-last_changed')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProjectsView, self).get_context_data(**kwargs)
        context['invites'] = Invite.objects.filter(user=self.request.user)
        context['is_site_manager'] = is_site_manager(self.request.user)
        return context


class SiteProjectsView(LoginRequiredMixin, FilterView):
    template_name = 'projects/site_projects.html'
    context_object_name = 'projects'
    paginate_by = 20
    filterset_class = ProjectFilter
    model = Project

    def get_queryset(self):
        if is_site_manager(self.request.user):
            # prepare projects queryset for the site manager
            queryset = Project.objects.filter_current_site()

            # prepare subquery for last_changed
            last_changed_subquery = models.Subquery(
                Value.objects.filter(project=models.OuterRef('pk')).order_by('-updated').values('updated')[:1]
            )
            queryset = queryset.annotate(last_changed=models.functions.Greatest('updated', last_changed_subquery))

            return queryset
        else:
            raise PermissionDenied()


class ProjectDetailView(ObjectPermissionMixin, DetailView):
    model = Project
    queryset = Project.objects.prefetch_related('issues', 'tasks', 'views')
    permission_required = 'projects.view_project_object'

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        project = context['project']
        ancestors = project.get_ancestors(include_self=True)

        highest = Membership.objects.filter(project__in=ancestors, user_id=OuterRef('user_id')).order_by('-project__level')
        memberships = Membership.objects.filter(project__in=ancestors) \
                                        .annotate(highest=Subquery(highest.values('project__level')[:1])) \
                                        .filter(highest=F('project__level')) \
                                        .select_related('user')

        integrations = Integration.objects.filter(project__in=ancestors)
        context['catalogs'] = Catalog.objects.filter_current_site() \
                                             .filter_group(self.request.user) \
                                             .filter_availability(self.request.user)
        context['memberships'] = memberships.order_by('user__last_name', '-project__level')
        context['integrations'] = integrations.order_by('provider_key', '-project__level')
        context['providers'] = get_plugins('SERVICE_PROVIDERS')
        context['issues'] = project.issues.active()
        context['snapshots'] = project.snapshots.all()
        context['invites'] = project.invites.all()
        context['membership'] = Membership.objects.filter(project=project, user=self.request.user).first()

        return context


class ProjectDeleteView(ObjectPermissionMixin, RedirectViewMixin, DeleteView):
    model = Project
    queryset = Project.objects.all()
    success_url = reverse_lazy('projects')
    permission_required = 'projects.delete_project_object'


class ProjectJoinView(LoginRequiredMixin, RedirectViewMixin, TemplateView):
    template_name = 'core/error.html'

    def get(self, request, token):
        try:
            invite = Invite.objects.get(token=token)

            if invite.is_expired:
                error = _('Sorry, your invitation has been expired.')
                invite.delete()
            elif invite.user and invite.user != request.user:
                error = _('Sorry, but this invitation is for the user "%s".' % invite.user)
            elif Membership.objects.filter(project=invite.project, user=request.user).exists():
                invite.delete()
                return redirect(invite.project.get_absolute_url())
            else:
                Membership.objects.create(
                    project=invite.project,
                    user=request.user,
                    role=invite.role
                )
                invite.delete()
                return redirect(invite.project.get_absolute_url())

        except Invite.DoesNotExist:
            error = _('Sorry, the invitation link is not valid.')

        return self.render_to_response({
            'title': _('Error'),
            'errors': [error]
        })


class ProjectCancelView(LoginRequiredMixin, RedirectViewMixin, TemplateView):
    template_name = 'core/error.html'
    success_url = reverse_lazy('projects')

    def get(self, request, token=None):
        invite = get_object_or_404(Invite, token=token)
        if invite.user in [None, request.user]:
            invite.delete()

        return redirect(self.success_url)


class ProjectLeaveView(ObjectPermissionMixin, RedirectViewMixin, FormMixin, DetailView):
    model = Project
    form_class = Form
    queryset = Project.objects.all()
    success_url = reverse_lazy('projects')
    permission_required = 'projects.leave_project_object'
    template_name = 'projects/project_confirm_leave.html'

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid() and 'cancel' not in request.POST:
            membership = Membership.objects.filter(project=self.get_object()).get(user=request.user)
            if not membership.is_last_owner:
                membership.delete()

        return redirect(self.success_url)


class ProjectExportView(ObjectPermissionMixin, DetailView):
    model = Project
    queryset = Project.objects.all()
    permission_required = 'projects.export_project_object'

    def render_to_response(self, context, **response_kwargs):
        export_plugin = get_plugin('PROJECT_EXPORTS', self.kwargs.get('format'))
        if export_plugin is None:
            raise Http404

        export_plugin.project = context['project']
        export_plugin.snapshot = None

        return export_plugin.render()


class ProjectQuestionsView(ObjectPermissionMixin, DetailView):
    model = Project
    queryset = Project.objects.all()
    permission_required = 'projects.view_project_object'
    template_name = 'projects/project_questions.html'

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.catalog is None:
            return redirect('project_error', pk=self.object.pk)
        else:
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)


class ProjectErrorView(ObjectPermissionMixin, DetailView):
    model = Project
    queryset = Project.objects.all()
    permission_required = 'projects.view_project_object'
    template_name = 'projects/project_error.html'
