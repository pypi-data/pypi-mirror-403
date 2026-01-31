"""
Integration tests using BaseCRUDTestCase for djadmin-filters plugin.

These tests verify that CRUD operations work with filtering, ordering, and search features.
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
    """Test Category CRUD operations with filters."""

    model = Category
    model_factory_class = CategoryFactory
    admin_site = site
    to_update_fields = {'name': 'Updated Category'}


class TestTagCRUD(BaseCRUDTestCase):
    """Test Tag CRUD operations with ordering."""

    model = Tag
    model_factory_class = TagFactory
    admin_site = site
    to_update_fields = {'name': 'Updated Tag'}


class TestProductCRUD(BaseCRUDTestCase):
    """Test Product CRUD operations with filters and ordering."""

    model = Product
    model_factory_class = ProductFactory
    admin_site = site
    to_update_fields = {'name': 'Updated Product'}


class TestCustomerCRUD(BaseCRUDTestCase):
    """Test Customer CRUD operations with filters and ordering."""

    model = Customer
    model_factory_class = CustomerFactory
    admin_site = site
    to_update_fields = {'first_name': 'Jane', 'last_name': 'Smith'}


class TestOrderCRUD(BaseCRUDTestCase):
    """Test Order CRUD operations with filters and ordering."""

    model = Order
    model_factory_class = OrderFactory
    admin_site = site
    to_update_fields = {'status': 'shipped'}


class TestOrderItemCRUD(BaseCRUDTestCase):
    """Test OrderItem CRUD operations with ordering."""

    model = OrderItem
    model_factory_class = OrderItemFactory
    admin_site = site
    to_update_fields = {'quantity': 5}


class TestReviewCRUD(BaseCRUDTestCase):
    """Test Review CRUD operations with filters and ordering."""

    model = Review
    model_factory_class = ReviewFactory
    admin_site = site
    to_update_fields = {'rating': 4, 'is_approved': False}
