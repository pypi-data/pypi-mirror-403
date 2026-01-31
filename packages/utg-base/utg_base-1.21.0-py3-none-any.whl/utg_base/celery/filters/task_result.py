from django_filters import rest_framework as filters


class TaskResultFilterSet(filters.FilterSet):
    status = filters.BooleanFilter()
