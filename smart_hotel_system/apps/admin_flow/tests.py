from django.test import TestCase
from common_flow.models import Order, Menu, Category, Table

# Create your tests here.
class AdminFlowTests(TestCase):
    def setUp(self):
        # Set up initial data for tests
        self.category = Category.objects.create(name="Beverages", description="Drinks and refreshments")
        self.menu_item = Menu.objects.create(
            title="Cappuccino",
            description="A classic Italian coffee drink",
            price=3.50,
            category=self.category,
            is_available=True
        )
        self.table = Table.objects.create(table_number=1, capacity=4)
