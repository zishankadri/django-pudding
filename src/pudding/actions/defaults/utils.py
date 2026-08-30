from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db import models


from django import forms
from django.db import models
from django.forms import modelform_factory

from pudding.forms import StyledModelForm


def formfield_for_dbfield(db_field, **kwargs):
    """Return a form field with widgets based on the model field type"""
    # Make a copy of kwargs because modelform_factory passes extra args
    formfield_kwargs = kwargs.copy()

    if isinstance(db_field, models.DateTimeField):
        formfield_kwargs["widget"] = forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        )
    elif isinstance(db_field, models.DateField):
        formfield_kwargs["widget"] = forms.DateInput(
            attrs={"type": "date"},
            format="%Y-%m-%d",
        )
    elif isinstance(db_field, models.TextField):
        formfield_kwargs["widget"] = forms.Textarea()

    formfield = db_field.formfield(**formfield_kwargs)

    # Ensure initial value formatting works
    if isinstance(db_field, (models.DateTimeField, models.DateField)):
        formfield.input_formats = [formfield.widget.format]

    return db_field.formfield(**formfield_kwargs)


def get_editable_fields(model, fields=None):
    """Return fields suitable for ModelForm, excluding non-editable fields"""
    all_fields = fields if fields else [f.name for f in model._meta.fields]
    editable_fields = [f for f in all_fields if model._meta.get_field(f).editable]

    return editable_fields


def get_form_class(
    *,
    model: type[models.Model],
    fields=None,
    exclude=None,
    form_class: type[forms.ModelForm[models.Model]] = StyledModelForm,
    widgets=None,
) -> type[forms.ModelForm[models.Model]]:
    fields = get_editable_fields(model, fields)

    return modelform_factory(
        model,
        form=form_class,
        fields=fields,
        exclude=exclude,
        widgets=widgets,
        formfield_callback=formfield_for_dbfield,
    )
