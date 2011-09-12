# -*- coding: utf-8 -*-
from django import forms
from redisco.models import FieldValidationError


def redisco_validate_wrapper(old_clean, new_clean):
    def inner_validate(instance, name, value):
        old_value = getattr(instance, name)
        value = old_clean(value)
        try:
            setattr(instance, name, value)
            new_clean(instance)
            setattr(instance, name, old_value)
            return value
        except FieldValidationError, e:
            setattr(instance, name, old_value)
            raise forms.ValidationError([e[1] for e in e.errors])
    return inner_validate

def iter_valid_fields(meta):
    meta_fields = getattr(meta, 'fields', ())
    meta_exclude = getattr(meta, 'exclude', ()) + ('_id',)

    for field_name, field in meta.model._attributes.iteritems():
        if (meta_fields and field_name not in meta_fields) or field_name in meta_exclude:
            continue
        yield (field_name, field)
