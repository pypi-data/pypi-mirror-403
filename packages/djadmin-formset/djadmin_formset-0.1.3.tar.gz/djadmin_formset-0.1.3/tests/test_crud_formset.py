"""
CRUD tests for djadmin-formset plugin using BaseCRUDTestCase.

Tests all 7 webshop models with FormCollection features.
"""

import factory
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


class CustomerWithOrdersFactory(CustomerFactory):
    """Customer factory that creates 2 orders by default."""

    @factory.post_generation
    def orders(obj, create, extracted, **kwargs):
        """Create orders after customer is created."""
        if not create:
            return
        
        # Create 2 orders for this customer
        OrderFactory.create_batch(2, customer=obj)


class TestCategoryCRUD(BaseCRUDTestCase):
    """Test CRUD operations for Category model."""

    model = Category
    model_factory_class = CategoryFactory
    admin_site = site
    to_update_fields = {'name': 'Updated Category'}


class TestTagCRUD(BaseCRUDTestCase):
    """Test CRUD operations for Tag model."""

    model = Tag
    model_factory_class = TagFactory
    admin_site = site
    to_update_fields = {'name': 'Updated Tag'}


class TestProductCRUD(BaseCRUDTestCase):
    """Test CRUD operations for Product model."""

    model = Product
    model_factory_class = ProductFactory
    admin_site = site
    to_update_fields = {'name': 'Updated Product'}


class TestCustomerCRUD(BaseCRUDTestCase):
    """Test CRUD operations for Customer model (with Collections)."""

    model = Customer
    model_factory_class = CustomerFactory
    admin_site = site
    to_update_fields = {'first_name': 'Jane', 'last_name': 'Smith'}


class TestOrderCRUD(BaseCRUDTestCase):
    """Test CRUD operations for Order model (with conditional/computed fields)."""

    model = Order
    model_factory_class = OrderFactory
    admin_site = site
    to_update_fields = {'status': 'shipped'}


class TestOrderItemCRUD(BaseCRUDTestCase):
    """Test CRUD operations for OrderItem model."""

    model = OrderItem
    model_factory_class = OrderItemFactory
    admin_site = site
    to_update_fields = {'quantity': 5}


class TestReviewCRUD(BaseCRUDTestCase):
    """Test CRUD operations for Review model."""

    model = Review
    model_factory_class = ReviewFactory
    admin_site = site
    to_update_fields = {'rating': 4, 'is_approved': False}


class TestCustomerWithOrdersCRUD(BaseCRUDTestCase):
    """Test editing Customer with populated orders Collection.
    
    This test specifically focuses on the Edit action to verify that:
    1. The form displays existing orders in the Collection
    2. Updating the customer and modifying orders works correctly
    """

    model = Customer
    model_factory_class = CustomerWithOrdersFactory
    admin_site = site
    to_update_fields = {'first_name': 'Jane', 'last_name': 'Smith'}

    def _get_all_actions(self):
        """Override to only test the Edit action."""
        model_admin = self._get_model_admin()
        # Only test Edit action (record action for updating)
        return [action for action in model_admin.record_actions if action.__class__.__name__ == 'EditAction']

    def test_collection_items_rendered_in_edit_form(self):
        """Test that existing orders are rendered in the edit form Collection."""
        # Create a customer with orders using our factory
        customer = self.model_factory_class.create()
        
        # Verify customer has 2 orders
        self.assertEqual(customer.orders.count(), 2)
        
        # Get the orders for verification
        orders = list(customer.orders.all())
        
        # Get the edit URL
        model_admin = self._get_model_admin()
        edit_action = [a for a in model_admin.record_actions if a.__class__.__name__ == 'EditAction'][0]
        url = self._get_action_url(edit_action, customer)
        
        # Make GET request to edit page
        response = self.client.get(url)
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        
        # Check that the Collection is present
        self.assertContains(response, 'Customer Orders')  # Collection legend
        
        # Check that both orders are rendered in the form
        # FormCollection renders orders with their IDs as hidden input fields
        for order in orders:
            # Check for order ID as hidden input: <input type="hidden" name="id" value="X">
            self.assertContains(response, f'name="id" value="{order.pk}"')
            # Check for order status in select dropdown (selected option)
            self.assertContains(response, f'value="{order.status}" selected')
            # Check for order total in number input
            self.assertContains(response, f'name="total" value="{order.total}"')
