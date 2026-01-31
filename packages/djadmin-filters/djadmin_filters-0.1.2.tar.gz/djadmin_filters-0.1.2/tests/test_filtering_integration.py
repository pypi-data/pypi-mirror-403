"""
Integration tests for filtering and sorting functionality.

These tests verify that the djadmin-filters plugin actually filters and sorts
data correctly when query parameters are passed to list views.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from djadmin import site
from core_webshop.factories import ProductFactory

User = get_user_model()


class TestProductFiltering(TestCase):
    """Test filtering on Product list view."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    def setUp(self):
        """Create test products with known attributes."""
        self.client.force_login(self.user)
        
        # Create products with specific attributes for testing
        self.active_product = ProductFactory(name='Active Product', status='active')
        self.draft_product = ProductFactory(name='Draft Product', status='draft')
        self.discontinued_product = ProductFactory(name='Discontinued Product', status='discontinued')

    def test_filter_by_status(self):
        """Test filtering products by status shows only matching products."""
        url = site.reverse('core_webshop_product_list')
        response = self.client.get(url, {'status': 'active'})
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Active product should be present
        self.assertIn('Active Product', content)
        
        # Draft and discontinued should not be present
        self.assertNotIn('Draft Product', content)
        self.assertNotIn('Discontinued Product', content)

    def test_filter_by_two_fields(self):
        """Test filtering by multiple fields works correctly."""
        # Create products with specific combinations
        from core_webshop.factories import CategoryFactory
        electronics = CategoryFactory(name='Electronics')
        books = CategoryFactory(name='Books')
        
        active_electronics = ProductFactory(
            name='Active Electronics',
            status='active',
            category=electronics
        )
        draft_electronics = ProductFactory(
            name='Draft Electronics',
            status='draft',
            category=electronics
        )
        active_books = ProductFactory(
            name='Active Books',
            status='active',
            category=books
        )
        
        url = site.reverse('core_webshop_product_list')
        response = self.client.get(url, {
            'category': electronics.pk,
            'status': 'active'
        })
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Only active electronics should be present
        self.assertIn('Active Electronics', content)
        self.assertNotIn('Draft Electronics', content)
        self.assertNotIn('Active Books', content)


class TestProductOrdering(TestCase):
    """Test ordering on Product list view."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    def setUp(self):
        """Create test products for ordering."""
        self.client.force_login(self.user)
        
        # Create products with specific names for alphabetical testing
        self.aardvark = ProductFactory(name='Aardvark Product')
        self.monkey = ProductFactory(name='Monkey Product')
        self.zebra = ProductFactory(name='Zebra Product')

    def test_order_by_name_ascending(self):
        """Test ordering products by name (A-Z)."""
        url = site.reverse('core_webshop_product_list')
        response = self.client.get(url, {'ordering': 'name'})
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Find positions in HTML
        aardvark_pos = content.find('Aardvark Product')
        monkey_pos = content.find('Monkey Product')
        zebra_pos = content.find('Zebra Product')
        
        # All should be present
        self.assertNotEqual(aardvark_pos, -1)
        self.assertNotEqual(monkey_pos, -1)
        self.assertNotEqual(zebra_pos, -1)
        
        # Verify alphabetical order (earlier in HTML = earlier in list)
        self.assertLess(aardvark_pos, monkey_pos, "Aardvark should come before Monkey")
        self.assertLess(monkey_pos, zebra_pos, "Monkey should come before Zebra")

    def test_order_by_name_descending(self):
        """Test ordering products by name (Z-A)."""
        url = site.reverse('core_webshop_product_list')
        response = self.client.get(url, {'ordering': '-name'})
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Find positions in HTML
        aardvark_pos = content.find('Aardvark Product')
        monkey_pos = content.find('Monkey Product')
        zebra_pos = content.find('Zebra Product')
        
        # All should be present
        self.assertNotEqual(aardvark_pos, -1)
        self.assertNotEqual(monkey_pos, -1)
        self.assertNotEqual(zebra_pos, -1)
        
        # Verify reverse alphabetical order
        self.assertLess(zebra_pos, monkey_pos, "Zebra should come before Monkey in descending order")
        self.assertLess(monkey_pos, aardvark_pos, "Monkey should come before Aardvark in descending order")


class TestProductCombined(TestCase):
    """Test combining filter, search, and ordering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    def setUp(self):
        """Create test products."""
        self.client.force_login(self.user)
        
        # Create products with searchable terms and different statuses
        self.laptop_active = ProductFactory(
            name='Gaming Laptop',
            description='High performance laptop',
            status='active'
        )
        self.laptop_draft = ProductFactory(
            name='Budget Laptop',
            description='Entry level laptop',
            status='draft'
        )
        self.mouse_active = ProductFactory(
            name='Gaming Mouse',
            description='RGB mouse',
            status='active'
        )

    def test_filter_and_search_and_order(self):
        """Test combining filter, search, and ordering in one request."""
        url = site.reverse('core_webshop_product_list')
        response = self.client.get(url, {
            'q': 'Gaming',  # Search for "Gaming"
            'status': 'active',  # Filter to active only
            'ordering': '-name'  # Order by name descending
        })
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Should show both active "Gaming" products
        mouse_pos = content.find('Gaming Mouse')
        laptop_pos = content.find('Gaming Laptop')
        
        self.assertNotEqual(mouse_pos, -1, "Gaming Mouse should be present")
        self.assertNotEqual(laptop_pos, -1, "Gaming Laptop should be present")
        
        # Should NOT show draft laptop
        self.assertNotIn('Budget Laptop', content)
        
        # Mouse should come before Laptop (descending order)
        self.assertLess(mouse_pos, laptop_pos, "Gaming Mouse should come before Gaming Laptop in descending order")


class TestUserFiltering(TestCase):
    """Test filtering on User list view from contrib_auth plugin."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    def setUp(self):
        """Create test users."""
        self.client.force_login(self.admin)
        
        # Create users with specific attributes
        self.staff_user = User.objects.create_user(
            username='staffmember',
            email='staff@example.com',
            password='pass123',
            is_staff=True,
            is_active=True
        )
        self.inactive_user = User.objects.create_user(
            username='inactiveuser',
            email='inactive@example.com',
            password='pass123',
            is_staff=False,
            is_active=False
        )

    def test_filter_and_search_users(self):
        """Test filtering and searching users simultaneously."""
        url = site.reverse('auth_user_list')
        response = self.client.get(url, {
            'q': 'staff',  # Search for "staff"
            'is_staff': 'true'  # Filter to staff only
        })
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Should show staff member
        self.assertIn('staffmember', content)
        
        # Should NOT show inactive user or admin (admin doesn't match "staff" search)
        # (admin is superuser which includes is_staff, but username doesn't match search)
        self.assertNotIn('inactiveuser', content)


class TestGroupFiltering(TestCase):
    """Test filtering on Group list view from contrib_auth plugin."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    def setUp(self):
        """Create test groups."""
        from django.contrib.auth.models import Group
        self.client.force_login(self.admin)
        
        # Create groups with specific names
        self.editors = Group.objects.create(name='Editors')
        self.viewers = Group.objects.create(name='Viewers')
        self.admins = Group.objects.create(name='Admins')

    def test_search_groups(self):
        """Test searching groups by name."""
        from django.contrib.auth.models import Group
        url = site.reverse('auth_group_list')
        response = self.client.get(url, {'q': 'Editor'})
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Should show Editors
        self.assertIn('Editors', content)
        
        # Should NOT show Viewers or Admins
        self.assertNotIn('Viewers', content)
        self.assertNotIn('Admins', content)
