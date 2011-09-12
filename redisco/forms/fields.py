# -*- coding: utf-8 -*-
from django import forms


class RediscoFormFieldGenerator(object):
    def generate(self, field_name, field):
        field_class_name = field.__class__.__name__
        if hasattr(self, 'generate_%s' % field_class_name.lower()):
            return getattr(self,
                'generate_%s' % field_class_name.lower())(field_name, field)
        else:
            raise NotImplementedError(
                '%s is not supported by RediscoForm' % field_class_name)

    def generate_attribute(self, field_name, field):
        return forms.CharField(
            required=field.required,
            initial=field.default,
            widget=forms.Textarea,
        )

    def generate_charfield(self, field_name, field):
        return forms.CharField(
            required=field.required,
            max_length=field.max_length,
            initial=field.default
        )

    def generate_integerfield(self, field_name, field):
        return forms.IntegerField(
            required=field.required,
            initial=field.default
        )

    def generate_floatfield(self, field_name, field):
        return forms.FloatField(
            required=field.required,
            initial=field.default
        )

    def generate_booleanfield(self, field_name, field):
        return forms.BooleanField(
            required=field.required,
            initial=field.default
        )

    def generate_datetimefield(self, field_name, field):
        return forms.DateTimeField(
            required=field.required,
            initial=field.default
        )

    def generate_datefield(self, field_name, field):
        return forms.DateField(
            required=field.required,
            initial=field.default
        )
