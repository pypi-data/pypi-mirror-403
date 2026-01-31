"""Pytest configuration for core-only integration tests."""

import pytest
from pytest_factoryboy import register

# Register all factories from core_webshop
from core_webshop.factories import (
    CategoryFactory,
    CustomerFactory,
    OrderFactory,
    OrderItemFactory,
    ProductFactory,
    ReviewFactory,
    TagFactory,
)

# Register factories as pytest fixtures
register(CategoryFactory)
register(TagFactory)
register(ProductFactory)
register(CustomerFactory)
register(OrderFactory)
register(OrderItemFactory)
register(ReviewFactory)


@pytest.fixture
def admin_client(client, django_user_model):
    """Authenticated admin client."""
    user = django_user_model.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='password',
    )
    client.force_login(user)
    return client
