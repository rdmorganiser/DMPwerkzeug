from rest_framework import serializers

from rdmo.projects.models import Project
from rdmo.questions.models import Catalog, QuestionSet, Section


class QuestionSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionSet
        fields = (
            'id',
            'title'
        )


class SectionSerializer(serializers.ModelSerializer):

    questionsets = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = (
            'id',
            'title',
            'questionsets'
        )

    def get_questionsets(self, obj):
        queryset = obj.questionsets.filter(questionset=None)
        serializer = QuestionSetSerializer(queryset, many=True)
        return serializer.data


class CatalogSerializer(serializers.ModelSerializer):

    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = Catalog
        fields = (
            'id',
            'title',
            'sections'
        )


class ProjectOverviewSerializer(serializers.ModelSerializer):

    catalog = CatalogSerializer()
    read_only = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id',
            'title',
            'catalog',
            'read_only'
        )

    def get_read_only(self, obj):
        request = self.context.get('request')

        if request:
            return not (request.user.has_perm('projects.add_value_object', obj) and
                        request.user.has_perm('projects.change_value_object', obj) and
                        request.user.has_perm('projects.delete_value_object', obj))
        else:
            return True
