"""
ModelAdmin registrations for core tests (NO third-party plugin features).

This demonstrates core djadmin functionality by extending base webshop admin
classes without adding any plugin-specific features.

AVAILABLE FEATURES (from built-in plugins):
- Basic list_display (Column without Filter)
- Layout API (Field, Fieldset, Row)
- Basic search (core plugin)
- Pagination (core plugin)

NOT AVAILABLE (requires third-party plugins):
- Filter (requires djadmin-filters plugin)
- Collection (requires djadmin-formset plugin)
- Conditional fields (requires djadmin-formset plugin)
- Computed fields (requires djadmin-formset plugin)
"""

from djadmin import register
from core_webshop.base_djadmin import (
    BaseCategoryAdmin,
    BaseCustomerAdmin,
    BaseOrderAdmin,
    BaseOrderItemAdmin,
    BaseProductAdmin,
    BaseReviewAdmin,
    BaseTagAdmin,
)
from core_webshop.models import Category, Customer, Order, OrderItem, Product, Review, Tag


@register(Category)
class CategoryAdmin(BaseCategoryAdmin):
    """Category admin - core features only (inherits everything from base)."""

    pass


@register(Tag)
class TagAdmin(BaseTagAdmin):
    """Tag admin - core features only (inherits everything from base)."""

    pass


@register(Product)
class ProductAdmin(BaseProductAdmin):
    """Product admin - core features only (inherits everything from base)."""

    pass


@register(Customer)
class CustomerAdmin(BaseCustomerAdmin):
    """Customer admin - core features only (inherits everything from base)."""

    pass


@register(Order)
class OrderAdmin(BaseOrderAdmin):
    """Order admin - core features only (inherits everything from base)."""

    pass


@register(OrderItem)
class OrderItemAdmin(BaseOrderItemAdmin):
    """OrderItem admin - core features only (inherits everything from base)."""

    pass


@register(Review)
class ReviewAdmin(BaseReviewAdmin):
    """Review admin - core features only (inherits everything from base)."""

    pass
