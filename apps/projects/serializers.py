from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from apps.core.serializers import MarkdownSerializerMixin
from apps.domain.models import AttributeEntity, Attribute, Option, Range, VerboseName, Condition
from apps.questions.models import QuestionEntity, Question

from .models import *


class ProjectsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'current_snapshot', 'catalog')


class ValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = Value
        fields = (
            'id',
            'snapshot',
            'attribute',
            'set_index',
            'collection_index',
            'text',
            'option'
        )


class QuestionEntityOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Option
        fields = (
            'id',
            'text',
            'additional_input'
        )


class QuestionEntityRangeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Range
        fields = (
            'id',
            'minimum',
            'maximum',
            'step'
        )


class QuestionEntityQuestionVerboseNameSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    name_plural = serializers.SerializerMethodField()

    class Meta:
        model = VerboseName
        fields = (
            'name',
            'name_plural'
        )

    def get_name(self, obj):
        return obj.name or _('set')

    def get_name_plural(self, obj):
        return obj.name_plural or _('sets')


class QuestionEntityVerboseNameSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    name_plural = serializers.SerializerMethodField()

    class Meta:
        model = VerboseName
        fields = (
            'name',
            'name_plural'
        )

    def get_name(self, obj):
        return obj.name or _('item')

    def get_name_plural(self, obj):
        return obj.name_plural or _('items')


class QuestionEntityConditionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Condition
        fields = (
            'id',
            'source_attribute',
            'relation',
            'target_text',
            'target_option'
        )


class QuestionEntityAttributeSerializer(MarkdownSerializerMixin, serializers.ModelSerializer):

    options = QuestionEntityOptionSerializer(many=True, read_only=True)
    range = QuestionEntityRangeSerializer(read_only=True)
    verbosename = QuestionEntityQuestionVerboseNameSerializer()

    conditions = QuestionEntityConditionSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = (
            'id',
            'options',
            'range',
            'verbosename',
            'conditions',
            'is_collection'
        )


class QuestionEntityAttributeEntitySerializer(MarkdownSerializerMixin, serializers.ModelSerializer):

    verbosename = QuestionEntityVerboseNameSerializer()

    conditions = QuestionEntityConditionSerializer(many=True, read_only=True)

    class Meta:
        model = AttributeEntity
        fields = (
            'id',
            'verbosename',
            'conditions'
        )


class QuestionEntityQuestionSerializer(MarkdownSerializerMixin, serializers.ModelSerializer):

    markdown_fields = ('help', )

    attribute = QuestionEntityAttributeSerializer(source='attribute_entity.attribute')

    class Meta:
        model = Question
        fields = (
            'id',
            'order',
            'text',
            'help',
            'widget_type',
            'attribute'
        )


class QuestionEntitySerializer(MarkdownSerializerMixin, serializers.ModelSerializer):

    markdown_fields = ('help', )

    attribute_entity = QuestionEntityAttributeEntitySerializer()

    collection = QuestionEntityAttributeEntitySerializer(source='attribute_entity.parent_collection')

    questions = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()

    next = serializers.SerializerMethodField()
    prev = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    section = serializers.CharField(source='subsection.section.title')
    subsection = serializers.CharField(source='subsection.title')

    class Meta:
        model = QuestionEntity
        fields = (
            'id',
            'help',
            'attribute_entity',
            'collection',
            'is_set',
            'next',
            'prev',
            'progress',
            'section',
            'subsection',
            'collection',
            'questions',
            'attributes'
        )

    def get_questions(self, obj):
        if obj.is_set:
            return QuestionEntityQuestionSerializer(instance=obj.questions, many=True, read_only=True).data
        else:
            return [QuestionEntityQuestionSerializer(instance=obj.question, read_only=True).data]

    def get_attributes(self, obj):
        if obj.is_set:
            if obj.attribute_entity.parent_collection_id:
                attributes = Attribute.objects.filter(parent_collection_id=obj.attribute_entity.parent_collection_id)
                return [attribute.id for attribute in attributes]
            else:
                return [question.attribute_entity_id for question in obj.questions.all()]
        else:
            return [obj.attribute_entity_id]

    def get_prev(self, obj):
        try:
            return QuestionEntity.objects.get_prev(obj.pk).pk
        except QuestionEntity.DoesNotExist:
            return None

    def get_next(self, obj):
        try:
            return QuestionEntity.objects.get_next(obj.pk).pk
        except QuestionEntity.DoesNotExist:
            return None

    def get_progress(self, obj):
        try:
            return QuestionEntity.objects.get_progress(obj.pk)
        except QuestionEntity.DoesNotExist:
            return None
