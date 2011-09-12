# -*- coding: utf-8 -*-
import types
from django import forms
from django.utils.datastructures import SortedDict

from redisco.models import Model

from fields import RediscoFormFieldGenerator
from utils import redisco_validate_wrapper, iter_valid_fields

__all__ = ('RediscoForm',)


class RediscoFormMetaClass(type):
    def __new__(cls, name, bases, attrs):
        fields = [(field_name, attrs.pop(field_name)) for field_name, obj in \
            attrs.items() if isinstance(obj, forms.Field)]
        fields.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))

        for base in bases[::-1]:
            if hasattr(base, 'base_fields'):
                fields = base.base_fields.items() + fields

        attrs['base_fields'] = SortedDict(fields)

        if ('Meta' in attrs and hasattr(attrs['Meta'], 'model')
            and issubclass(attrs['Meta'].model, Model)):
            doc_fields = SortedDict()

            formfield_generator = getattr(attrs['Meta'], 'formfield_generator',
                RediscoFormFieldGenerator)()

            for field_name, field in iter_valid_fields(attrs['Meta']):
                doc_fields[field_name] = formfield_generator.generate(
                    field_name, field)
                doc_fields[field_name].clean = redisco_validate_wrapper(
                    doc_fields[field_name].clean, field.validate)

            doc_fields.update(attrs['base_fields'])
            attrs['base_fields'] = doc_fields

        attrs['_meta'] = attrs.get('Meta', object())

        return super(RediscoFormMetaClass, cls).__new__(cls, name, bases, attrs)

class RediscoForm(forms.BaseForm):
    __metaclass__ = RediscoFormMetaClass

    def __init__(self, data=None, auto_id='id_%s', prefix=None, initial=None,
        error_class=forms.util.ErrorList, label_suffix=':',
        empty_permitted=False, instance=None):

        assert isinstance(instance, (types.NoneType, Model)), \
            'instance must be a mongoengine document, ' \
            'not %s' % type(instance).__name__

        assert hasattr(self, 'Meta'), 'Meta class is needed to use RediscoForm'

        if instance is None:
            if self._meta.model is None:
                raise ValueError('RediscoForm has no model class specified.')
            self.instance = self._meta.model()
            object_data = {}
            self.instance._adding = True
        else:
            self.instance = instance
            self.instance._adding = False
            object_data = {}

            for field_name, field in iter_valid_fields(self._meta):
                field_data = getattr(instance, field_name)
                object_data[field_name] = field_data

        if initial is not None:
            object_data.update(initial)

        self._validate_unique = False
        super(RediscoForm, self).__init__(data, None, auto_id, prefix,
            object_data, error_class, label_suffix, empty_permitted)

    def _clean_fields(self):
        for name, field in self.fields.items():
            value = field.widget.value_from_datadict(
                self.data, self.files, self.add_prefix(name))
            try:
                value = field.clean(self.instance, name, value)
                self.cleaned_data[name] = value
                if hasattr(self, 'clean_%s' % name):
                    value = getattr(self, 'clean_%s' % name)()
                    self.cleaned_data[name] = value
            except forms.ValidationError, e:
                self._errors[name] = self.error_class(e.messages)
                if name in self.cleaned_data:
                    del self.cleaned_data[name]


    def save(self, commit=True):
        for field_name, field in iter_valid_fields(self._meta):
            setattr(self.instance, field_name,
                self.cleaned_data.get(field_name))

        if commit:
            self.instance.save()

        return self.instance
