from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, filters
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND

from apps.core.views import ProtectedCreateView, ProtectedUpdateView, ProtectedDeleteView
from apps.core.utils import render_to_format
from apps.tasks.models import Task


from .models import Project
from .serializers import *


@login_required()
def projects(request):
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'projects/projects.html', {'projects': projects})


@login_required()
def project(request, pk):
    project = get_object_or_404(Project.objects.filter(owner=request.user), pk=pk)

    tasks = []
    for task in Task.objects.all():
        for condition in task.conditions.all():
            if condition.resolve(project.current_snapshot):
                tasks.append({
                    'title': task.title,
                    'text': task.text,
                    'deadline': task.get_deadline(project.current_snapshot),
                })

    return render(request, 'projects/project.html', {
        'project': project,
        'tasks': tasks
    })


@login_required()
def project_summary(request, pk):
    project = get_object_or_404(Project.objects.filter(owner=request.user), pk=pk)

    return render(request, 'projects/project_summary.html', {
        'project': project,
        'export_formats': settings.EXPORT_FORMATS
    })


@login_required()
def project_summary_export(request, pk, format):
    project = get_object_or_404(Project.objects.filter(owner=request.user), pk=pk)

    return render_to_format(request, 'projects/project_summary_pdf.html', {
        'project': project
    }, project.title, format)


class ProjectCreateView(ProtectedCreateView):
    model = Project
    fields = ['title', 'description', 'catalog']

    def form_valid(self, form):
        response = super(ProjectCreateView, self).form_valid(form)

        # add current user as owner
        form.instance.owner.add(self.request.user)

        return response


class ProjectUpdateView(ProtectedUpdateView):
    model = Project
    fields = ['title', 'description', 'catalog']

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


class ProjectDeleteView(ProtectedDeleteView):
    model = Project
    success_url = reverse_lazy('projects')

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


@login_required()
def project_questions(request, project_id):
    return render(request, 'projects/project_questions.html', {
        'project_id': project_id
    })


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )

    serializer_class = ProjectsSerializer

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


class ValueViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )

    serializer_class = ValueSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = (
        'snapshot',
        'attribute',
        'attribute__parent_collection'
    )

    def get_queryset(self):
        return Value.objects \
            .filter(snapshot__project__owner=self.request.user) \
            .order_by('set_index', 'collection_index')


class QuestionEntityViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (DjangoModelPermissions, )

    queryset = QuestionEntity.objects.filter(question__parent_entity=None)
    serializer_class = QuestionEntitySerializer

    @list_route(methods=['get'], permission_classes=[DjangoModelPermissions])
    def first(self, request, pk=None):
        try:
            catalog = Catalog.objects.get(pk=request.GET.get('catalog'))
            entity = QuestionEntity.objects.order_by_catalog(catalog).first()
            serializer = self.get_serializer(entity)
            return Response(serializer.data)
        except Catalog.DoesNotExist as e:
            return Response({'message': e.message}, status=HTTP_404_NOT_FOUND)

    @detail_route(methods=['get'], permission_classes=[DjangoModelPermissions])
    def prev(self, request, pk=None):
        try:
            return Response({'id': QuestionEntity.objects.get_prev(pk).pk})
        except QuestionEntity.DoesNotExist as e:
            return Response({'message': e.message}, status=HTTP_404_NOT_FOUND)

    @detail_route(methods=['get'], permission_classes=[DjangoModelPermissions])
    def next(self, request, pk=None):
        try:
            return Response({'id': QuestionEntity.objects.get_next(pk).pk})
        except QuestionEntity.DoesNotExist as e:
            return Response({'message': e.message}, status=HTTP_404_NOT_FOUND)


class CatalogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated, )

    queryset = Catalog.objects.all()
    serializer_class = CatalogSerializer
