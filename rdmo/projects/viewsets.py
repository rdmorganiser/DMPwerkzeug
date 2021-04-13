from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.mixins import (CreateModelMixin, ListModelMixin,
                                   RetrieveModelMixin, UpdateModelMixin)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                     ReadOnlyModelViewSet)
from rest_framework_extensions.cache.mixins import RetrieveCacheResponseMixin
from rest_framework_extensions.mixins import NestedViewSetMixin

from rdmo.conditions.models import Condition
from rdmo.core.permissions import HasModelPermission, HasObjectPermission
from rdmo.core.utils import human2bytes, return_file_response
from rdmo.options.models import OptionSet
from rdmo.questions.models import Catalog, Question, QuestionSet

from .filters import SnapshotFilterBackend, ValueFilterBackend
from .models import (Continuation, Integration, Issue, Membership, Project,
                     Snapshot, Value)
from .serializers.v1 import (IntegrationSerializer, IssueSerializer,
                             MembershipSerializer,
                             ProjectIntegrationSerializer,
                             ProjectIssueSerializer,
                             ProjectMembershipSerializer,
                             ProjectMembershipUpdateSerializer,
                             ProjectSerializer, ProjectSnapshotSerializer,
                             ProjectValueSerializer, SnapshotSerializer,
                             ValueSerializer)
from .serializers.v1.overview import ProjectOverviewSerializer
from .serializers.v1.questionset import QuestionSetSerializer


class ProjectViewSet(ModelViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = ProjectSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (
        'title',
        'user',
        'user__username',
        'catalog',
        'catalog__uri',
        'catalog__key',
    )

    def get_queryset(self):
        return Project.objects.filter_user(self.request.user)

    @action(detail=True, permission_classes=(IsAuthenticated, ))
    def overview(self, request, pk=None):
        project = self.get_object()
        project.catalog = Catalog.objects.prefetch_related(
            'sections',
            'sections__questionsets',
            'sections__questionsets__questions'
        ).get(id=project.catalog_id)

        serializer = ProjectOverviewSerializer(project, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, permission_classes=(HasModelPermission | HasObjectPermission, ))
    def resolve(self, request, pk=None):
        try:
            condition = Condition.objects.get(pk=request.GET.get('condition'))
            return Response({'result': condition.resolve(self.get_object(), None)})
        except Condition.DoesNotExist:
            return Response({'result': False})

    @action(detail=True, permission_classes=(HasModelPermission | HasObjectPermission, ))
    def options(self, request, pk=None):
        project = self.get_object()

        try:
            optionset = OptionSet.objects.get(pk=request.GET.get('optionset'))

            # check if the optionset belongs to this catalog and if it has a provider
            if Question.objects.filter_by_catalog(project.catalog).filter(optionsets=optionset) and \
                    optionset.provider is not None:
                options = optionset.provider.get_options(project)
                return Response(options)

        except OptionSet.DoesNotExist:
            pass

        # if it didn't work return 404
        raise NotFound()

    @action(detail=True, permission_classes=(IsAuthenticated, ))
    def progress(self, request, pk=None):
        project = self.get_object()
        return Response(project.progress)

    def perform_create(self, serializer):
        project = serializer.save(site=get_current_site(self.request))

        # add current user as owner
        membership = Membership(project=project, user=self.request.user, role='owner')
        membership.save()


class ProjectNestedViewSetMixin(NestedViewSetMixin):

    def initial(self, request, *args, **kwargs):
        self.project = self.get_project_from_parent_viewset()
        super().initial(request, *args, **kwargs)

    def get_project_from_parent_viewset(self):
        try:
            return Project.objects.filter_user(self.request.user).get(pk=self.get_parents_query_dict().get('project'))
        except Project.DoesNotExist:
            raise Http404

    def get_list_permission_object(self):
        return self.project

    def get_detail_permission_object(self, obj):
        return self.project

    def perform_create(self, serializer):
        serializer.save(project=self.project)


class ProjectMembershipViewSet(ProjectNestedViewSetMixin, ModelViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )

    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'user',
        'user__username',
        'role'
    )

    def get_queryset(self):
        try:
            return Membership.objects.filter(project=self.project)
        except AttributeError:
            # this is needed for the swagger ui
            return Membership.objects.none()

    def get_serializer_class(self):
        if self.action == 'update':
            return ProjectMembershipUpdateSerializer
        else:
            return ProjectMembershipSerializer


class ProjectIntegrationViewSet(ProjectNestedViewSetMixin, ModelViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = ProjectIntegrationSerializer

    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'provider_key',
    )

    def get_queryset(self):
        try:
            return Integration.objects.filter(project=self.project)
        except AttributeError:
            # this is needed for the swagger ui
            return Integration.objects.none()


class ProjectIssueViewSet(ProjectNestedViewSetMixin, ListModelMixin, RetrieveModelMixin,
                          UpdateModelMixin, GenericViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = ProjectIssueSerializer

    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'task',
        'task__uri',
        'status'
    )

    def get_queryset(self):
        try:
            return Issue.objects.filter(project=self.project).prefetch_related('resources')
        except AttributeError:
            # this is needed for the swagger ui
            return Issue.objects.none()


class ProjectSnapshotViewSet(ProjectNestedViewSetMixin, CreateModelMixin, RetrieveModelMixin,
                             UpdateModelMixin, ListModelMixin, GenericViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = ProjectSnapshotSerializer

    def get_queryset(self):
        try:
            return self.project.snapshots.all()
        except AttributeError:
            # this is needed for the swagger ui
            return Snapshot.objects.none()


class ProjectValueViewSet(ProjectNestedViewSetMixin, ModelViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = ProjectValueSerializer

    filter_backends = (ValueFilterBackend, DjangoFilterBackend)
    filterset_fields = (
        'attribute',
        'attribute__path',
        'option',
        'option__path',
    )

    def get_queryset(self):
        try:
            return self.project.values.filter(snapshot=None)
        except AttributeError:
            # this is needed for the swagger ui
            return Value.objects.none()

    @action(detail=True, methods=['GET', 'POST'],
            permission_classes=(HasModelPermission | HasObjectPermission, ))
    def file(self, request, parent_lookup_project, pk=None):
        value = self.get_object()

        if request.method == 'POST':
            value.file = request.FILES.get('file')

            # check if the project is reached
            if value.file and value.file.size + value.project.file_size > human2bytes(settings.PROJECT_FILE_QUOTA):
                raise serializers.ValidationError({
                    'value': [_('You reached the file quota for this project.')]
                })

            value.save()
            serializer = self.get_serializer(value)
            return Response(serializer.data)

        else:
            if value.file:
                return return_file_response(value.file.name, value.file_type)

        # if it didn't work return 404
        raise NotFound()


class ProjectQuestionSetViewSet(ProjectNestedViewSetMixin, RetrieveCacheResponseMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = QuestionSetSerializer

    def get_queryset(self):
        return QuestionSet.objects.order_by_catalog(self.project.catalog)

    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)

        if response.status_code == 200 and kwargs.get('pk'):
            try:
                continuation = Continuation.objects.get(project=self.project, user=self.request.user)
            except Continuation.DoesNotExist:
                continuation = Continuation(project=self.project, user=self.request.user)

            continuation.questionset_id = kwargs.get('pk')
            continuation.save()

        return response

    @action(detail=False, url_path='continue', permission_classes=(IsAuthenticated, ))
    def get_continue(self, request, pk=None, parent_lookup_project=None):
        try:
            continuation = Continuation.objects.get(project=self.project, user=self.request.user)

            if continuation.questionset.section.catalog == self.project.catalog:
                questionset = continuation.questionset
            else:
                questionset = self.get_queryset().first()

        except Continuation.DoesNotExist:
            questionset = self.get_queryset().first()

        serializer = self.get_serializer(questionset)
        return Response(serializer.data)


class MembershipViewSet(ReadOnlyModelViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = MembershipSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (
        'user',
        'user__username',
        'role'
    )

    def get_queryset(self):
        return Membership.objects.filter_user(self.request.user)

    def get_detail_permission_object(self, obj):
        return obj.project


class IntegrationViewSet(ReadOnlyModelViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = IntegrationSerializer

    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'project',
        'provider_key'
    )

    def get_queryset(self):
        return Integration.objects.filter_user(self.request.user)

    def get_detail_permission_object(self, obj):
        return obj.project


class IssueViewSet(ReadOnlyModelViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = IssueSerializer

    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'task',
        'task__uri',
        'status'
    )

    def get_queryset(self):
        return Issue.objects.filter_user(self.request.user).prefetch_related('resources')

    def get_detail_permission_object(self, obj):
        return obj.project


class SnapshotViewSet(ReadOnlyModelViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = SnapshotSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (
        'title',
        'project'
    )

    def get_queryset(self):
        return Snapshot.objects.filter_user(self.request.user)

    def get_detail_permission_object(self, obj):
        return obj.project


class ValueViewSet(ReadOnlyModelViewSet):
    permission_classes = (HasModelPermission | HasObjectPermission, )
    serializer_class = ValueSerializer

    filter_backends = (SnapshotFilterBackend, DjangoFilterBackend)
    filterset_fields = (
        'project',
        'attribute',
        'attribute__path',
        'option',
        'option__path',
    )

    def get_queryset(self):
        return Value.objects.filter_user(self.request.user)

    def get_detail_permission_object(self, obj):
        return obj.project

    @action(detail=True, permission_classes=(HasModelPermission | HasObjectPermission, ))
    def file(self, request, pk=None):
        value = self.get_object()

        if value.file:
            return return_file_response(value.file.name, value.file_type)

        # if it didn't work return 404
        raise NotFound()
