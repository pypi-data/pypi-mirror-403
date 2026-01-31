from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from utg_base.utils.date import to_udate, to_udatetime
from utg_base.utils.translation import translate as _


class UDateField(serializers.DateField):
    def to_internal_value(self, value):
        return to_udate(super().to_internal_value(value))


class UDateTimeField(serializers.DateTimeField):
    def to_internal_value(self, value):
        return to_udatetime(super().to_internal_value(value))


class DateSerializer(serializers.Serializer):
    dt = UDateField()


class DatePeriodSerializer(DateSerializer):
    period = serializers.ChoiceField(choices=['daily', 'monthly', 'yearly'], default='daily')


class DateTimePeriodSerializer(DateSerializer):
    dt = UDateTimeField(required=False)
    period = serializers.ChoiceField(choices=['hourly', 'today', 'daily', 'monthly', 'yearly'], default='daily')

    def validate(self, attrs):
        period = attrs.get('period', 'daily')
        dt = attrs.get('dt')

        if period != 'today' and dt is None:
            raise ValidationError({
                'dt': _('This field is required when period is not "today".')
            })
        return attrs


class RelatedObjectField(serializers.PrimaryKeyRelatedField):
    """
    POST / PUT  -> UUID (string)
    RESPONSE    -> {id, name}
    """
    fields = []

    def __init__(self, **kwargs):
        self.fields = kwargs.pop("fields", ("id", "name"))
        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return {field: getattr(value, field) for field in self.fields}
