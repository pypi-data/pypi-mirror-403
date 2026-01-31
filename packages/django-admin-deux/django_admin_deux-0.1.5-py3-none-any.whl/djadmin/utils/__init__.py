"""Utility classes and functions for djadmin."""

from .metaclasses import SingletonMeta
from .repr import ReprMixin, auto_repr

__all__ = ['SingletonMeta', 'ReprMixin', 'auto_repr']
