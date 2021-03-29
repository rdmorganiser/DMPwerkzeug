from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from rdmo.conditions.models import Condition
from rdmo.core.serializers import MarkdownSerializerMixin
from rdmo.domain.models import Attribute
from rdmo.options.models import Option, OptionSet
from rdmo.questions.models import Question, QuestionSet


class OptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Option
        fields = (
            'id',
            'text',
            'additional_input'
        )


class OptionSetSerializer(serializers.ModelSerializer):

    options = OptionSerializer(many=True)
    provider = serializers.SerializerMethodField()

    class Meta:
        model = OptionSet
        fields = (
            'id',
            'provider',
            'options',
            'conditions'
        )

    def get_provider(self, obj):
        return obj.provider is not None


class AttributeSerializer(MarkdownSerializerMixin, serializers.ModelSerializer):

    id_attribute = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = (
            'id',
            'id_attribute',
        )

    def get_id_attribute(self, obj):
        try:
            return {'id': obj.children.get(key='id').pk}
        except Attribute.DoesNotExist:
            return None


class ConditionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Condition
        fields = (
            'id',
            'source',
            'relation',
            'target_text',
            'target_option'
        )


class QuestionSerializer(MarkdownSerializerMixin, serializers.ModelSerializer):

    markdown_fields = ('help', )

    attribute = AttributeSerializer(default=None)
    optionsets = serializers.SerializerMethodField()

    verbose_name = serializers.SerializerMethodField()
    verbose_name_plural = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            'id',
            'order',
            'help',
            'text',
            'default_text',
            'verbose_name',
            'verbose_name_plural',
            'widget_type',
            'value_type',
            'unit',
            'minimum',
            'maximum',
            'step',
            'attribute',
            'optionsets',
            'is_collection',
            'is_optional'
        )

    def get_optionsets(self, obj):
        return OptionSetSerializer(obj.optionsets.order_by('order'), many=True).data

    def get_verbose_name(self, obj):
        return obj.verbose_name or _('item')

    def get_verbose_name_plural(self, obj):
        return obj.verbose_name_plural or _('items')


class QuestionSetSerializer(MarkdownSerializerMixin, serializers.ModelSerializer):

    markdown_fields = ('help', )

    questions = QuestionSerializer(many=True)

    next = serializers.SerializerMethodField()
    prev = serializers.SerializerMethodField()

    section = serializers.SerializerMethodField()

    attribute = AttributeSerializer()

    conditions = ConditionSerializer(default=None, many=True)

    verbose_name = serializers.SerializerMethodField()
    verbose_name_plural = serializers.SerializerMethodField()

    class Meta:
        model = QuestionSet
        fields = (
            'id',
            'title',
            'help',
            'verbose_name',
            'verbose_name_plural',
            'attribute',
            'is_collection',
            'next',
            'prev',
            'section',
            'questions',
            'conditions'
        )

    def get_prev(self, obj):
        try:
            return QuestionSet.objects.get_prev(obj.pk).pk
        except QuestionSet.DoesNotExist:
            return None

    def get_next(self, obj):
        try:
            return QuestionSet.objects.get_next(obj.pk).pk
        except QuestionSet.DoesNotExist:
            return None

    def get_section(self, obj):
        return {
            'id': obj.section.id,
            'title': obj.section.title
        }

    def get_verbose_name(self, obj):
        return obj.verbose_name or _('set')

    def get_verbose_name_plural(self, obj):
        return obj.verbose_name_plural or _('sets')
