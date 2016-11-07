import factory

from factory.django import DjangoModelFactory

from apps.options.testing.factories import OptionSetFactory

from ..models import *


class AttributeEntityFactory(DjangoModelFactory):

    class Meta:
        model = AttributeEntity

    title = 'title'
    is_collection = False


class AttributeFactory(DjangoModelFactory):

    class Meta:
        model = Attribute

    title = 'title'
    is_collection = False

    value_type = 'text'

    @factory.post_generation
    def post_generation(self, create, extracted, **kwargs):
        if self.value_type == 'options':
            optionset = OptionSetFactory()
            self.optionsets.add(optionset)
            self.save()

        elif self.value_type == 'range':
            RangeFactory(id=20000 + self.id, attribute=self)


class VerboseNameFactory(DjangoModelFactory):

    class Meta:
        model = VerboseName

    attribute_entity = factory.SubFactory(AttributeEntityFactory)

    name_en = 'name_en'
    name_de = 'name_de'

    name_plural_en = 'name_plural_en'
    name_plural_de = 'name_plural_de'


class RangeFactory(DjangoModelFactory):

    class Meta:
        model = Range

    attribute = factory.SubFactory('apps.domain.testing.factories.AttributeFactory')

    minimum = 0.0
    maximum = 100.0
    step = 10
