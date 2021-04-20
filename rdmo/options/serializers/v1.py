from rest_framework import serializers
from rest_framework.reverse import reverse

from rdmo.conditions.models import Condition
from rdmo.core.serializers import TranslationSerializerMixin
from rdmo.core.utils import get_language_warning
from rdmo.questions.models import QuestionSet

from ..models import Option, OptionSet
from ..validators import (OptionLockedValidator, OptionSetLockedValidator,
                          OptionSetUniqueURIValidator,
                          OptionUniqueURIValidator)


class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionSet
        fields = (
            'id',
            'uri'
        )


class ConditionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Condition
        fields = (
            'id',
            'uri'
        )


class OptionSetSerializer(serializers.ModelSerializer):

    key = serializers.SlugField(required=True)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = OptionSet
        fields = (
            'id',
            'uri',
            'uri_prefix',
            'key',
            'comment',
            'locked',
            'order',
            'provider_key',
            'conditions',
            'questions'
        )
        validators = (
            OptionSetUniqueURIValidator(),
            OptionSetLockedValidator()
        )


class OptionSerializer(TranslationSerializerMixin, serializers.ModelSerializer):

    key = serializers.SlugField(required=True)
    optionset = serializers.PrimaryKeyRelatedField(queryset=OptionSet.objects.all(), required=True)
    conditions = ConditionSerializer(many=True, read_only=True)
    values_count = serializers.IntegerField(read_only=True)
    projects_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Option
        fields = (
            'id',
            'optionset',
            'uri',
            'uri_prefix',
            'key',
            'comment',
            'locked',
            'order',
            'text',
            'label',
            'additional_input',
            'conditions',
            'values_count',
            'projects_count'
        )
        trans_fields = (
            'text',
        )
        validators = (
            OptionUniqueURIValidator(),
            OptionLockedValidator()
        )


class OptionSetIndexOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Option
        fields = (
            'id',
            'uri'
        )


class OptionSetIndexSerializer(serializers.ModelSerializer):

    options = OptionSetIndexOptionSerializer(many=True)

    class Meta:
        model = OptionSet
        fields = (
            'id',
            'uri',
            'options'
        )


class OptionIndexSerializer(serializers.ModelSerializer):

    class Meta:
        model = Option
        fields = (
            'id',
            'optionset',
            'uri',
            'text'
        )


class ConditionNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Condition
        fields = (
            'id',
            'uri'
        )


class ProviderNestedSerializer(serializers.Serializer):

    key = serializers.CharField()
    label = serializers.CharField()
    class_name = serializers.CharField()

    class Meta:
        fields = (
            'key',
            'label',
            'class_name'
        )


class OptionNestedSerializer(serializers.ModelSerializer):

    warning = serializers.SerializerMethodField()
    xml_url = serializers.SerializerMethodField()

    class Meta:
        model = Option
        fields = (
            'id',
            'uri',
            'uri_prefix',
            'path',
            'locked',
            'order',
            'text',
            'warning',
            'xml_url'
        )

    def get_warning(self, obj):
        return get_language_warning(obj, 'text')

    def get_xml_url(self, obj):
        return reverse('v1-options:option-detail-export', args=[obj.pk])


class OptionSetNestedSerializer(serializers.ModelSerializer):

    options = OptionNestedSerializer(many=True)
    conditions = ConditionNestedSerializer(many=True)
    provider = ProviderNestedSerializer()
    xml_url = serializers.SerializerMethodField()

    class Meta:
        model = OptionSet
        fields = (
            'id',
            'uri',
            'uri_prefix',
            'key',
            'order',
            'locked',
            'provider',
            'options',
            'conditions',
            'xml_url'
        )

    def get_xml_url(self, obj):
        return reverse('v1-options:optionset-detail-export', args=[obj.pk])
