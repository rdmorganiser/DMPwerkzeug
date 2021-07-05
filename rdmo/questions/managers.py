from django.db import models

from rdmo.core.managers import (AvailabilityManagerMixin,
                                AvailabilityQuerySetMixin,
                                CurrentSiteManagerMixin,
                                CurrentSiteQuerySetMixin, GroupsManagerMixin,
                                GroupsQuerySetMixin)


class CatalogQuestionSet(CurrentSiteQuerySetMixin, GroupsQuerySetMixin, AvailabilityQuerySetMixin, models.QuerySet):

    def filter_catalog(self, catalog):
        return self.filter(models.Q(catalogs=None) | models.Q(catalogs=catalog))


class CatalogManager(CurrentSiteManagerMixin, GroupsManagerMixin, AvailabilityManagerMixin, models.Manager):

    def get_queryset(self):
        return CatalogQuestionSet(self.model, using=self._db)

    def filter_catalog(self, catalog):
        return self.get_queryset().filter_catalog(catalog)


class QuestionSetQuerySet(models.QuerySet):

    def order_by_catalog(self, catalog):
        return self.filter(section__catalog=catalog, questionset=None).order_by('section__order', 'order')

    def filter_by_catalog(self, catalog):
        return self.filter(section__catalog=catalog)


class QuestionSetManager(models.Manager):

    def get_queryset(self):
        return QuestionSetQuerySet(self.model, using=self._db)

    def order_by_catalog(self, catalog):
        return self.get_queryset().order_by_catalog(catalog)

    def filter_by_catalog(self, catalog):
        return self.get_queryset().filter_by_catalog(catalog)


class QuestionQuerySet(models.QuerySet):

    def order_by_catalog(self, catalog):
        return self.filter(questionset__section__catalog=catalog).order_by('questionset__section__order', 'questionset__order', 'order')

    def filter_by_catalog(self, catalog):
        return self.filter(questionset__section__catalog=catalog)


class QuestionManager(models.Manager):

    def get_queryset(self):
        return QuestionQuerySet(self.model, using=self._db)

    def order_by_catalog(self, catalog):
        return self.get_queryset().order_by_catalog(catalog)

    def filter_by_catalog(self, catalog):
        return self.get_queryset().filter_by_catalog(catalog)
