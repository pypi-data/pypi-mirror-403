"""Repr utilities for djadmin classes."""

import inspect


def auto_repr(*attrs):
    """Decorator that adds a clean __repr__ method to a class.

    Introspects __init__ signature and shows only non-default values.
    Handles special formatting for model classes and other Django objects.

    Can be used with or without arguments:
        @auto_repr  # Show all non-default __init__ params
        class MyClass:
            ...

        @auto_repr('model')  # Only show 'model' attribute
        class MyClass:
            ...

    Example:
        @auto_repr
        class MyClass:
            def __init__(self, name, model, optional=None):
                self.name = name
                self.model = model
                self.optional = optional

        obj = MyClass('test', MyModel)
        repr(obj)  # "MyClass(name='test', model=myapp.MyModel)"
    """

    def decorator(cls):
        # Store attrs on the class for the __repr__ method
        cls._repr_attrs = attrs if attrs else None

        def __repr__(self):
            return _generate_repr(self)

        cls.__repr__ = __repr__
        return cls

    # Handle both @auto_repr and @auto_repr('model') syntax
    if len(attrs) == 1 and isinstance(attrs[0], type):
        # Called as @auto_repr without parens - attrs[0] is the class
        cls = attrs[0]
        cls._repr_attrs = None

        def __repr__(self):
            return _generate_repr(self)

        cls.__repr__ = __repr__
        return cls

    return decorator


def _generate_repr(obj):
    """Generate repr string for an object.

    Args:
        obj: Object instance with _repr_attrs attribute

    Returns:
        String representation
    """
    class_name = obj.__class__.__name__
    attrs = getattr(obj, '_repr_attrs', None)

    # If _repr_attrs is set, only show those attributes
    if attrs:
        parts = []
        for attr_name in attrs:
            value = getattr(obj, attr_name, None)
            if value is not None:
                formatted = _format_repr_value(attr_name, value)
                parts.append(f'{attr_name}={formatted}')
        return f"{class_name}({', '.join(parts)})"

    # Get __init__ signature
    try:
        sig = inspect.signature(obj.__init__)
    except (ValueError, TypeError):
        # Fallback if signature inspection fails
        return f'{class_name}()'

    parts = []

    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue

        # Skip *args and **kwargs
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue

        # Get current value
        value = getattr(obj, param_name, None)

        # Get default value
        default = param.default

        # Skip if value equals default
        if default is not inspect.Parameter.empty:
            try:
                if value == default:
                    continue
            except Exception:
                # If comparison fails, include the value
                pass

        # Format the value
        formatted = _format_repr_value(param_name, value)
        parts.append(f'{param_name}={formatted}')

    return f"{class_name}({', '.join(parts)})"


def _format_repr_value(name, value):
    """Format a value for repr output.

    Args:
        name: Parameter name
        value: Parameter value

    Returns:
        String representation of the value
    """
    # Handle None
    if value is None:
        return 'None'

    # Handle Django model classes
    if hasattr(value, '_meta') and hasattr(value._meta, 'label'):
        return value._meta.label

    # Handle classes (not instances)
    if isinstance(value, type):
        if hasattr(value, '_meta') and hasattr(value._meta, 'label'):
            return value._meta.label
        return value.__name__

    # Handle callables (functions, lambdas, methods)
    if callable(value):
        name = getattr(value, '__name__', None)
        if name:
            # Check if it's a lambda
            if name == '<lambda>':
                return '<lambda>'
            # Check if it's a method (has __self__)
            if hasattr(value, '__self__'):
                return f'{value.__self__.__class__.__name__}.{name}()'
            return f'{name}()'
        return '<callable>'

    # Handle lists/tuples of callables or other values
    if isinstance(value, list | tuple):
        formatted_items = [_format_repr_value(name, item) for item in value]
        if len(formatted_items) > 1:
            # Pretty print with newlines for multiple items
            indent = '    '
            items_str = f',\n{indent}'.join(formatted_items)
            if isinstance(value, tuple):
                return f'(\n{indent}{items_str}\n)'
            return f'[\n{indent}{items_str}\n]'
        else:
            # Single item or empty - keep inline
            if isinstance(value, tuple):
                return f"({', '.join(formatted_items)})"
            return f"[{', '.join(formatted_items)}]"

    # Default: use repr
    return repr(value)


# Keep ReprMixin for backward compatibility during transition
class ReprMixin:
    """Deprecated: Use @auto_repr decorator instead."""

    _repr_attrs = None

    def __repr__(self):
        return _generate_repr(self)
