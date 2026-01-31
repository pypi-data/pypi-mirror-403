"""
Form building utilities for the Layout API.

Provides the FormBuilder class that creates Django ModelForm classes from Layout definitions.
This is the core piece that makes layouts functional by generating actual forms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.forms import ModelForm

if TYPE_CHECKING:
    from django.db import models

    from djadmin.layout import Field, Layout


class LayoutAwareForm(ModelForm):
    """
    Base form that automatically applies Field configurations from Layout API.

    This form automatically applies Field definitions from the layout
    (label, widget, required, show_if, hide_if, calculate, attrs, etc.)
    during initialization.

    The form expects a `_field_definitions` class attribute containing a list
    of Field objects to configure.

    Handles readonly (disabled) fields properly:
    - Displays them in the form for viewing
    - Excludes them from cleaned_data to prevent overwriting with NULL values

    Example:
        class MyForm(LayoutAwareForm):
            _field_definitions = [
                Field('name', label='Full Name', required=True),
                Field('email', widget=EmailInput),
            ]

            class Meta:
                model = User
                fields = ['name', 'email']
                disabled_fields = ['created_at']  # Optional: readonly fields
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply Field configurations if provided
        if hasattr(self, '_field_definitions'):
            for field_def in self._field_definitions:
                self._apply_field_config(field_def)

    def clean(self):
        """
        Clean form data and remove disabled fields from cleaned_data.

        Disabled fields should be displayed for viewing but never saved.
        This prevents overwriting model values with NULL or stale data.
        """
        cleaned_data = super().clean()

        # Get list of disabled fields from Meta
        disabled_fields = getattr(self.Meta, 'disabled_fields', [])

        # Remove disabled fields from cleaned_data so they don't get saved
        for field_name in disabled_fields:
            cleaned_data.pop(field_name, None)

        return cleaned_data

    def _apply_field_config(self, field_def: Field):
        """
        Apply Field configuration to this form's field.

        Args:
            field_def: The Field definition from the layout
        """
        if field_def.name not in self.fields:
            return

        form_field = self.fields[field_def.name]

        # Apply basic configurations
        if field_def.label is not None:
            form_field.label = field_def.label

        if field_def.widget is not None:
            if isinstance(field_def.widget, type):
                form_field.widget = field_def.widget()
            else:
                form_field.widget = field_def.widget

        if field_def.required is not None:
            form_field.required = field_def.required

        if field_def.help_text is not None:
            form_field.help_text = field_def.help_text

        if field_def.initial is not None:
            form_field.initial = field_def.initial

        # Apply django-formset features (if used with plugin)
        if field_def.show_if:
            form_field.widget.attrs['df-show'] = field_def.show_if

        if field_def.hide_if:
            form_field.widget.attrs['df-hide'] = field_def.hide_if

        if field_def.calculate:
            form_field.widget.attrs['df-calculate'] = field_def.calculate

        # Apply custom attrs
        if field_def.attrs:
            form_field.widget.attrs.update(field_def.attrs)

        # Apply extra_kwargs
        for key, value in field_def.extra_kwargs.items():
            setattr(form_field, key, value)


class FormBuilder:
    """
    Build Django ModelForm classes from Layout definitions.

    Core implementation that works without plugins. Generates standard ModelForm
    instances with field customizations from the Layout API.

    Example:
        layout = Layout(
            Field('name', label='Product Name'),
            Field('price', widget='number'),
        )

        form_class = FormBuilder.from_layout(layout, Product)
        form = form_class()
    """

    @staticmethod
    def _separate_editable_fields(model: type[models.Model], fields: list[str]) -> tuple[list[str], list[str]]:
        """
        Separate field list into editable and readonly (non-editable) fields.
        
        Args:
            model: Django model class
            fields: List of field names to categorize
            
        Returns:
            Tuple of (editable_fields, readonly_fields)
        """
        editable_fields = []
        readonly_fields = []

        for field_name in fields:
            try:
                model_field = model._meta.get_field(field_name)
                target = editable_fields if model_field.editable else readonly_fields
                target.append(field_name)
            except Exception:
                # Not a model field (method, property, etc.) - add to editable fields
                editable_fields.append(field_name)
        
        return editable_fields, readonly_fields

    @classmethod
    def create_form(
        cls, model: type[models.Model], fields, base_form: type[ModelForm] | None = None
    ) -> type[ModelForm]:
        """
        Create form class from fields (no layout).

        This is used when no layout is provided and we need to generate a form
        from a list of field names. Handles non-editable (readonly) fields by:
        1. Creating base form with editable fields only
        2. Adding readonly fields as disabled form fields
        3. Populating their values from instance in __init__

        Args:
            model: Django model class
            fields: List of field names or '__all__'
            base_form: Optional base form class to inherit from

        Returns:
            Generated ModelForm class with readonly fields included

        Example:
            FormClass = FormBuilder.create_form(Product, fields=['name', 'price', 'order_number'])
            form = FormClass(instance=product)  # order_number populated even if editable=False
        """
        from django.forms import modelform_factory

        # Expand '__all__' to actual field list
        if fields == '__all__':
            fields = [
                f.name for f in model._meta.get_fields() if not f.auto_created and (f.editable or not f.many_to_many)
            ]

        # Separate editable from non-editable fields
        editable_fields, readonly_fields = FormBuilder._separate_editable_fields(model, fields)

        # Create base form with editable fields only
        # Django will raise FieldError if we include non-editable fields in Meta.fields
        base = modelform_factory(model, form=base_form or ModelForm, fields=editable_fields or '__all__')

        # If no readonly fields, return as-is
        if not readonly_fields:
            return base

        # Add readonly fields as disabled form fields
        readonly_form_fields = {}
        for field_name in readonly_fields:
            try:
                model_field = model._meta.get_field(field_name)
                form_field = model_field.formfield()
                if form_field:
                    form_field.disabled = True
                    form_field.required = False  # Disabled fields should not be required
                    readonly_form_fields[field_name] = form_field
            except Exception:
                # Can't create form field - skip
                pass

        # Create a new Meta class with disabled_fields attribute
        # We inherit from the base form's Meta and add disabled_fields
        meta_attrs = {
            'model': base.Meta.model,
            'fields': base.Meta.fields,
            'disabled_fields': readonly_fields,  # CRITICAL: Add readonly fields list
        }

        # Create new Meta class using type()
        new_meta_class = type('Meta', (base.Meta,), meta_attrs)

        # Create unique form class name based on fields to avoid caching/reuse issues
        # Multiple forms with same name would share _meta even though they have different fields
        import hashlib

        fields_hash = hashlib.md5('_'.join(sorted(editable_fields + readonly_fields)).encode()).hexdigest()[:8]
        form_class_name = f'{model.__name__}Form_{fields_hash}'

        def custom_init(self, *args, **kwargs):
            base.__init__(self, *args, **kwargs)
            self._meta.disabled_fields = self.Meta.disabled_fields

            # Populate readonly fields from instance
            if self.instance and self.instance.pk and hasattr(self, 'fields'):
                for field_name in self.Meta.disabled_fields:
                    if field_name in self.fields:
                        try:
                            # Get value from model instance
                            model_field = model._meta.get_field(field_name)
                            value = model_field.value_from_object(self.instance)

                            # Prepare value using form field's prepare_value
                            form_field = self.fields[field_name]
                            prepared_value = form_field.prepare_value(value)

                            # Set in initial dict (used by BoundField for rendering)
                            self.initial[field_name] = prepared_value
                        except Exception:
                            pass

        form_class = type(
            form_class_name,
            (base,),
            {
                **readonly_form_fields,
                'Meta': new_meta_class,
                # '__init__': custom_init,
            },
        )

        return form_class

    @staticmethod
    def from_layout(
        layout: Layout,
        model: type[models.Model],
        base_form: type[ModelForm] | None = None,
    ) -> type[ModelForm]:
        """
        Build a ModelForm class from a Layout definition.

        Creates a standard Django ModelForm with field customizations from the layout.
        The generated form includes:
        - Meta class with model and fields list
        - Field configurations (label, widget, required, help_text, initial)
        - _layout attribute for template rendering

        Args:
            layout: Layout definition with Field components
            model: Django model class
            base_form: Optional base form class (defaults to ModelForm)

        Returns:
            Generated ModelForm class ready for instantiation

        Example:
            layout = Layout(
                Field('name', label='Full Name', required=True),
                Field('bio', widget='textarea'),
            )

            FormClass = FormBuilder.from_layout(layout, Author)
            form = FormClass()
        """
        base = base_form or ModelForm

        # Extract field names from layout
        field_names = FormBuilder._extract_field_names(layout)
        
        # Separate editable from readonly fields (Django doesn't allow non-editable fields in Meta.fields)
        editable_fields, readonly_fields = FormBuilder._separate_editable_fields(model, field_names)

        # Build form class attributes
        form_attrs: dict[str, Any] = {
            'djadmin_layout': layout,  # Store for template rendering (no underscore - Django templates don't allow it)
            'Meta': type(
                'Meta',
                (),
                {
                    'model': model,
                    'fields': editable_fields,  # Only editable fields in Meta.fields
                    'disabled_fields': readonly_fields,  # Track readonly fields for clean() method
                },
            ),
        }

        # Build field configurations from layout
        field_configs = {}
        for field_def in FormBuilder._iterate_fields(layout):
            config = FormBuilder._build_field_config(field_def)
            if config:
                field_configs[field_def.name] = config
        
        # Add readonly fields as disabled form fields
        readonly_form_fields = {}
        for field_name in readonly_fields:
            try:
                model_field = model._meta.get_field(field_name)
                form_field = model_field.formfield()
                if form_field:
                    form_field.disabled = True
                    form_field.required = False  # Disabled fields should not be required
                    readonly_form_fields[field_name] = form_field
            except Exception:
                # Can't create form field - skip
                pass

        # Merge readonly fields into form_attrs
        form_attrs.update(readonly_form_fields)

        # Create form class
        form_class = type(
            f'{model.__name__}Form',
            (base,),
            form_attrs,
        )

        # Customize __init__ to apply field configurations
        original_init = form_class.__init__

        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)

            # Apply field customizations
            for field_name, config in field_configs.items():
                if field_name in self.fields:
                    for attr_name, attr_value in config.items():
                        # Special handling for widget: instantiate if it's a class
                        if attr_name == 'widget' and isinstance(attr_value, type):
                            attr_value = attr_value()
                        setattr(self.fields[field_name], attr_name, attr_value)

        form_class.__init__ = new_init

        return form_class

    @staticmethod
    def _build_field_config(field_def: Field) -> dict[str, Any]:
        """
        Build field configuration dict from Field definition.

        Extracts field attributes (label, widget, required, help_text, initial)
        and any extra_kwargs into a configuration dict.

        Args:
            field_def: Field component from layout

        Returns:
            Dict of field attributes to apply

        Example:
            field = Field('name', label='Full Name', required=True)
            config = _build_field_config(field)
            # Returns: {'label': 'Full Name', 'required': True}
        """
        config: dict[str, Any] = {}

        # Standard field attributes
        if field_def.label is not None:
            config['label'] = field_def.label

        if field_def.widget is not None:
            # Widget can be class, instance, or resolved from shortcut
            config['widget'] = field_def.widget

        if field_def.required is not None:
            config['required'] = field_def.required

        if field_def.help_text is not None:
            config['help_text'] = field_def.help_text

        if field_def.initial is not None:
            config['initial'] = field_def.initial

        # Merge extra_kwargs (allows arbitrary form field kwargs)
        config.update(field_def.extra_kwargs)

        return config

    @staticmethod
    def _extract_field_names(layout: Layout) -> list[str]:
        """
        Extract field names from layout recursively.

        Traverses the layout structure and collects all field names from
        Field components. Handles nested structures (Fieldset, Row).
        Does NOT include Collection fields (those require plugin support).

        Args:
            layout: Layout to extract from

        Returns:
            List of field names in order of appearance

        Example:
            layout = Layout(
                Fieldset('Info',
                    Field('name'),
                    Row(Field('city'), Field('state')),
                ),
            )
            names = _extract_field_names(layout)
            # Returns: ['name', 'city', 'state']
        """
        from djadmin.layout import Field, Fieldset, Row

        names: list[str] = []

        def extract(item):
            """Recursively extract field names."""
            if isinstance(item, Field):
                names.append(item.name)
            elif isinstance(item, Fieldset | Row):
                for field in item.fields:
                    extract(field)
            # Note: Collections are NOT processed here (require plugin)

        for item in layout.items:
            extract(item)

        return names

    @staticmethod
    def _iterate_fields(layout: Layout):
        """
        Iterate all Field objects in layout recursively.

        Generator that yields Field components from the layout structure.
        Handles nested structures (Fieldset, Row).
        Does NOT yield Collection fields (those require plugin support).

        Args:
            layout: Layout to iterate

        Yields:
            Field objects in order of appearance

        Example:
            layout = Layout(
                Field('name'),
                Fieldset('Address',
                    Field('street'),
                    Field('city'),
                ),
            )

            for field in _iterate_fields(layout):
                print(field.name)
            # Prints: name, street, city
        """
        from djadmin.layout import Field, Fieldset, Row

        def iterate(item):
            """Recursively iterate Field objects."""
            if isinstance(item, Field):
                yield item
            elif isinstance(item, Fieldset | Row):
                for field in item.fields:
                    yield from iterate(field)
            # Note: Collections are NOT processed here (require plugin)

        for item in layout.items:
            yield from iterate(item)
