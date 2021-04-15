from django.conf import settings
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from rdmo.core.exports import XMLResponse
from rdmo.core.permissions import HasModelPermission
from rdmo.core.views import ChoicesViewSet
from rdmo.core.viewsets import CopyModelMixin

from .models import Option, OptionSet
from .renderers import OptionRenderer, OptionSetRenderer
from .serializers.export import (OptionExportSerializer,
                                 OptionSetExportSerializer)
from .serializers.v1 import (OptionIndexSerializer, OptionSerializer,
                             OptionSetIndexSerializer,
                             OptionSetNestedSerializer, OptionSetSerializer)


class OptionSetViewSet(CopyModelMixin, ModelViewSet):
    permission_classes = (HasModelPermission, )
    queryset = OptionSet.objects.order_by('order').prefetch_related(
        'conditions',
        'questions',
        'options'
    )
    serializer_class = OptionSetSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (
        'uri',
        'key',
        'comment'
    )

    @action(detail=False)
    def nested(self, request):
        serializer = OptionSetNestedSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=False)
    def index(self, request):
        serializer = OptionSetIndexSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=False, permission_classes=[HasModelPermission])
    def export(self, request):
        serializer = OptionSetExportSerializer(self.get_queryset(), many=True)
        xml = OptionSetRenderer().render(serializer.data)
        return XMLResponse(xml, name='optionsets')

    @action(detail=True, url_path='export', permission_classes=[HasModelPermission])
    def detail_export(self, request, pk=None):
        serializer = OptionSetExportSerializer(self.get_object())
        xml = OptionSetRenderer().render([serializer.data])
        return XMLResponse(xml, name=self.get_object().key)


class OptionViewSet(CopyModelMixin, ModelViewSet):
    permission_classes = (HasModelPermission, )
    queryset = Option.objects.order_by('optionset__order', 'order') \
                             .annotate(values_count=models.Count('values')) \
                             .annotate(projects_count=models.Count('values__project', distinct=True)) \
                             .select_related('optionset') \
                             .prefetch_related('conditions')
    serializer_class = OptionSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (
        'uri',
        'key',
        'optionset',
        'comment'
    )

    @action(detail=False)
    def index(self, request):
        serializer = OptionIndexSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=False, permission_classes=[HasModelPermission])
    def export(self, request):
        serializer = OptionExportSerializer(self.get_queryset(), many=True)
        xml = OptionRenderer().render(serializer.data)
        return XMLResponse(xml, name='options')

    @action(detail=True, url_path='export', permission_classes=[HasModelPermission])
    def detail_export(self, request, pk=None):
        serializer = OptionExportSerializer(self.get_object())
        xml = OptionRenderer().render([serializer.data])
        return XMLResponse(xml, name=self.get_object().path)


class ProviderViewSet(ChoicesViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = settings.OPTIONSET_PROVIDERS
