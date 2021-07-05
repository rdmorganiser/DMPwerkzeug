import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.exceptions import \
    ValidationError as RestFameworkValidationError

from ..models import Question, QuestionSet
from ..serializers.v1 import QuestionSerializer
from ..validators import QuestionUniqueURIValidator


def test_unique_uri_validator_create(db):
    QuestionUniqueURIValidator()({
        'uri_prefix': settings.DEFAULT_URI_PREFIX,
        'key': 'test',
        'questionset': QuestionSet.objects.first()
    })


def test_unique_uri_validator_create_error(db):
    questionset = QuestionSet.objects.first()

    with pytest.raises(ValidationError):
        QuestionUniqueURIValidator()({
            'uri_prefix': settings.DEFAULT_URI_PREFIX,
            'key': questionset.questions.first().key,
            'questionset': questionset
        })


def test_unique_uri_validator_create_error2(db):
    # get a questionset which contains a questionset
    questionset = QuestionSet.objects.exclude(questionset=None).first().questionset

    with pytest.raises(ValidationError):
        QuestionUniqueURIValidator()({
            'uri_prefix': settings.DEFAULT_URI_PREFIX,
            'key': questionset.questionsets.first().key,
            'questionset': questionset
        })


def test_unique_uri_validator_update(db):
    question = Question.objects.first()

    QuestionUniqueURIValidator(question)({
        'uri_prefix': question.uri_prefix,
        'key': question.key,
        'questionset': question.questionset
    })


def test_unique_uri_validator_update_error(db):
    question = Question.objects.get(pk=18)

    with pytest.raises(ValidationError):
        QuestionUniqueURIValidator(question)({
            'uri_prefix': question.uri_prefix,
            'key': question.questionset.questions.last().key,
            'questionset': question.questionset
        })


def test_unique_uri_validator_serializer_create(db):
    validator = QuestionUniqueURIValidator()
    validator.set_context(QuestionSerializer())

    validator({
        'uri_prefix': settings.DEFAULT_URI_PREFIX,
        'key': 'test',
        'questionset': QuestionSet.objects.first()
    })


def test_unique_uri_validator_serializer_create_error(db):
    questionset = QuestionSet.objects.first()

    validator = QuestionUniqueURIValidator()
    validator.set_context(QuestionSerializer())

    with pytest.raises(RestFameworkValidationError):
        validator({
            'uri_prefix': settings.DEFAULT_URI_PREFIX,
            'key': questionset.questions.last().key,
            'questionset': questionset
        })


def test_unique_uri_validator_serializer_create_error2(db):
    # get a questionset which contains a questionset
    questionset = QuestionSet.objects.exclude(questionset=None).first().questionset

    validator = QuestionUniqueURIValidator()
    validator.set_context(QuestionSerializer())

    with pytest.raises(RestFameworkValidationError):
        validator({
            'uri_prefix': settings.DEFAULT_URI_PREFIX,
            'key': questionset.questionsets.first().key,
            'questionset': questionset
        })


def test_unique_uri_validator_serializer_update(db):
    question = Question.objects.first()

    validator = QuestionUniqueURIValidator()
    validator.set_context(QuestionSerializer(instance=question))

    validator({
        'uri_prefix': question.uri_prefix,
        'key': question.key,
        'questionset': question.questionset
    })


def test_unique_uri_validator_serializer_update_error(db):
    question = Question.objects.get(pk=18)

    validator = QuestionUniqueURIValidator()
    validator.set_context(QuestionSerializer(instance=question))

    with pytest.raises(RestFameworkValidationError):
        validator({
            'uri_prefix': question.uri_prefix,
            'key': question.questionset.questions.last().key,
            'questionset': question.questionset
        })
