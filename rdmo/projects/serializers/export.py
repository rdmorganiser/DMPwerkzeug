import base64

from rest_framework import serializers

from ..models import Project, Snapshot, Value


class ValueSerializer(serializers.ModelSerializer):

    attribute = serializers.CharField(source='attribute.uri', default=None, read_only=True)
    option = serializers.CharField(source='option.uri', default=None, read_only=True)
    file_content = serializers.SerializerMethodField()

    class Meta:
        model = Value
        fields = (
            'attribute',
            'set_prefix',
            'set_index',
            'collection_index',
            'text',
            'option',
            'file_name',
            'file_content',
            'value_type',
            'unit',
            'external_id',
            'created',
            'updated'
        )

    def get_file_content(self, obj):
        if obj.file:
            return base64.b64encode(obj.file.read())


class SnapshotSerializer(serializers.ModelSerializer):

    values = serializers.SerializerMethodField()

    class Meta:
        model = Snapshot
        fields = (
            'title',
            'description',
            'values',
            'created',
            'updated'
        )

    def get_values(self, obj):
        values = Value.objects.filter(snapshot=obj)
        serializer = ValueSerializer(instance=values, many=True)
        return serializer.data


class ProjectSerializer(serializers.ModelSerializer):

    snapshots = SnapshotSerializer(many=True)
    values = serializers.SerializerMethodField()

    catalog = serializers.CharField(source='catalog.uri', default=None, read_only=True)
    tasks = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'title',
            'description',
            'catalog',
            'tasks',
            'views',
            'snapshots',
            'values',
            'created',
            'updated'
        )

    def get_values(self, obj):
        values = Value.objects.filter(project=obj, snapshot=None)
        serializer = ValueSerializer(instance=values, many=True)
        return serializer.data

    def get_tasks(self, obj):
        return [task.uri for task in obj.tasks.all()]

    def get_views(self, obj):
        return [view.uri for view in obj.views.all()]
