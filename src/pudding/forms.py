from django import forms

FIELD_CLASSES = {
    "TextInput": "form-input",
    "NumberInput": "form-input",
    "Textarea": "form-text-area",
    "Select": "form-input",
    "DateInput": "form-input",
    "DateTimeInput": "form-input",
    "CheckboxInput": "h-4 w-4 text-blue-600 border-gray-300 roundedfocus:ring-2 focus:ring-blue-500",
    "ClearableFileInput": "form-input",
}


def apply_tailwind_classes(form: forms.BaseForm):
    for field in form.fields.values():
        widget = field.widget
        widget_type = widget.__class__.__name__

        existing_classes = widget.attrs.get("class", "")
        tailwind_classes = FIELD_CLASSES.get(widget_type, "form-input")

        widget.attrs["class"] = f"{existing_classes} {tailwind_classes}".strip()


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        apply_tailwind_classes(form=self)


class StyledForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        apply_tailwind_classes(form=self)
