"""
Integration tests using BaseCRUDTestCase for core features (NO third-party plugins).

These tests verify that core CRUD operations work without any third-party plugins.
Only built-in plugins (theme, contrib_auth, core) are available.
"""

from djadmin import site
from djadmin.testing import BaseCRUDTestCase
from core_webshop.factories import (
    CategoryFactory,
    CustomerFactory,
    OrderFactory,
    OrderItemFactory,
    ProductFactory,
    ReviewFactory,
    TagFactory,
)
from core_webshop.models import Category, Customer, Order, OrderItem, Product, Review, Tag


class TestCategoryCRUD(BaseCRUDTestCase):
    """Test Category CRUD operations (core features only)."""

    model = Category
    model_factory_class = CategoryFactory
    admin_site = site
    to_update_fields = {'name': 'Updated Category'}


class TestTagCRUD(BaseCRUDTestCase):
    """Test Tag CRUD operations (core features only)."""

    model = Tag
    model_factory_class = TagFactory
    admin_site = site
    to_update_fields = {'name': 'Updated Tag'}


class TestProductCRUD(BaseCRUDTestCase):
    """Test Product CRUD operations (core features only, no filters/formset)."""

    model = Product
    model_factory_class = ProductFactory
    admin_site = site
    to_update_fields = {'name': 'Updated Product'}  # price is Decimal, avoid type mismatch


class TestCustomerCRUD(BaseCRUDTestCase):
    """Test Customer CRUD operations (core features only)."""

    model = Customer
    model_factory_class = CustomerFactory
    admin_site = site
    to_update_fields = {'first_name': 'Jane', 'last_name': 'Smith'}


class TestOrderCRUD(BaseCRUDTestCase):
    """Test Order CRUD operations (core features only)."""

    model = Order
    model_factory_class = OrderFactory
    admin_site = site
    to_update_fields = {'status': 'shipped'}


class TestOrderItemCRUD(BaseCRUDTestCase):
    """Test OrderItem CRUD operations (core features only)."""

    model = OrderItem
    model_factory_class = OrderItemFactory
    admin_site = site
    to_update_fields = {'quantity': 5}


class TestReviewCRUD(BaseCRUDTestCase):
    """Test Review CRUD operations (core features only)."""

    model = Review
    model_factory_class = ReviewFactory
    admin_site = site
    to_update_fields = {'rating': 4, 'is_approved': False}
