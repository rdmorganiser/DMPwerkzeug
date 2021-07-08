from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from rdmo.core.validators import (InstanceValidator, LockedValidator,
                                  UniqueURIValidator)

from .models import Catalog, Question, QuestionSet, Section


class CatalogUniqueURIValidator(UniqueURIValidator):

    model = Catalog

    def get_uri(self, data):
        if not data.get('key'):
            self.raise_validation_error({'key': _('This field is required.')})
        else:
            uri = self.model.build_uri(data.get('uri_prefix'), data.get('key'))
            return uri


class SectionUniqueURIValidator(UniqueURIValidator):

    model = Section

    def get_uri(self, data):
        if not data.get('key'):
            self.raise_validation_error({'key': _('This field is required.')})
        elif not data.get('catalog'):
            self.raise_validation_error({'catalog': _('This field may not be null.')})
        else:
            path = self.model.build_path(data.get('key'), data.get('catalog'))
            uri = self.model.build_uri(data.get('uri_prefix'), path)
            return uri


class QuestionSetUniqueURIValidator(UniqueURIValidator):

    def __call__(self, data):
        uri = self.get_uri(data)
        self.validate(QuestionSet, self.instance, uri)
        self.validate(Question, self.instance, uri)

    def get_uri(self, data):
        if not data.get('key'):
            self.raise_validation_error({'key': _('This field is required.')})
        elif not data.get('section'):
            self.raise_validation_error({'section': _('This field may not be null.')})
        else:
            path = QuestionSet.build_path(data.get('key'), data.get('section'), data.get('questionset'))
            uri = QuestionSet.build_uri(data.get('uri_prefix'), path)
            return uri


class QuestionUniqueURIValidator(UniqueURIValidator):

    def __call__(self, data):
        uri = self.get_uri(data)
        self.validate(Question, self.instance, uri)
        self.validate(QuestionSet, self.instance, uri)

    def get_uri(self, data):
        if not data.get('key'):
            self.raise_validation_error({'key': _('This field is required.')})
        elif not data.get('questionset'):
            self.raise_validation_error({'questionset': _('This field may not be null.')})
        else:
            path = Question.build_path(data.get('key'), data.get('questionset'))
            uri = Question.build_uri(data.get('uri_prefix'), path)
            return uri


class QuestionSetQuestionSetValidator(InstanceValidator):

    def __call__(self, data):
        questionset = data.get('questionset')
        if questionset:
            if self.serializer:
                # check copied attributes
                view = self.serializer.context.get('view')
                if view and view.action == 'copy':
                    # get the original from the view when cloning an attribute
                    if questionset in view.get_object().get_descendants(include_self=True):
                        self.raise_validation_error({
                            'questionset': [_('A question set may not be cloned to be a child of itself or one of its descendants.')]
                        })

            # only check updated attributes
            if self.instance:
                if questionset in self.instance.get_descendants(include_self=True):
                    self.raise_validation_error({
                        'questionset': [_('A question set may not be moved to be a child of itself or one of its descendants.')]
                    })



class CatalogLockedValidator(LockedValidator):

    pass


class SectionLockedValidator(LockedValidator):

    parent_field = 'catalog'


class QuestionSetLockedValidator(LockedValidator):

    parent_field = 'section'


class QuestionLockedValidator(LockedValidator):

    parent_field = 'questionset'
