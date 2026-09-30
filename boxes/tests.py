from django.test import TestCase

# Create your tests here.
from decimal import Decimal

from rest_framework.test import APITestCase

from django.test import SimpleTestCase

from .models import Box, Order, OrderItem, Product
from .services import recommend_box


def make_product(name, length, width, height, weight):
    return Product(
        name=name,
        length_cm=Decimal(str(length)),
        width_cm=Decimal(str(width)),
        height_cm=Decimal(str(height)),
        weight_kg=Decimal(str(weight)),
    )


def make_box(name, length, width, height, max_weight, cost):
    return Box(
        name=name,
        inner_length_cm=Decimal(str(length)),
        inner_width_cm=Decimal(str(width)),
        inner_height_cm=Decimal(str(height)),
        max_weight_kg=Decimal(str(max_weight)),
        cost=Decimal(str(cost)),
    )


class RecommendBoxLogicTests(SimpleTestCase):
    """Unit tests for the pure selection logic (no database needed)."""

    def test_cheapest_valid_box_is_chosen(self):
        item = make_product("Mug", 10, 10, 10, 0.5)
        boxes = [
            make_box("Large", 50, 50, 50, 20, 30),
            make_box("Small", 20, 20, 20, 5, 10),
        ]
        rec = recommend_box([(item, 1)], boxes)
        self.assertEqual(rec.box.name, "Small")

    def test_weight_limit_rejects_box(self):
        item = make_product("Anvil", 10, 10, 10, 8)
        boxes = [
            make_box("Light", 30, 30, 30, 5, 5),
            make_box("Heavy", 30, 30, 30, 20, 15),
        ]
        rec = recommend_box([(item, 1)], boxes)
        self.assertEqual(rec.box.name, "Heavy")
        self.assertIn("Light", rec.rejected)

    def test_weight_exactly_at_limit_is_allowed(self):
        item = make_product("Block", 10, 10, 10, 5)
        rec = recommend_box([(item, 1)], [make_box("Exact", 30, 30, 30, 5, 10)])
        self.assertEqual(rec.box.name, "Exact")

    def test_quantity_multiplies_weight(self):
        item = make_product("Bottle", 5, 5, 5, 1)
        boxes = [make_box("Tiny", 30, 30, 30, 2, 5), make_box("Sturdy", 30, 30, 30, 10, 9)]
        rec = recommend_box([(item, 3)], boxes)   # 3 kg total
        self.assertEqual(rec.box.name, "Sturdy")

    def test_rotation_allows_item_to_fit(self):
        # 30x10x5 only fits the 12x6x35 box if it is rotated.
        item = make_product("Rod", 30, 10, 5, 0.2)
        rec = recommend_box([(item, 1)], [make_box("Tall", 12, 6, 35, 5, 10)])
        self.assertIsNotNone(rec.box)

    def test_item_too_large_for_every_box(self):
        item = make_product("Surfboard", 200, 50, 10, 4)
        rec = recommend_box([(item, 1)], [make_box("Medium", 40, 30, 20, 10, 20)])
        self.assertIsNone(rec.box)
        self.assertIn("Medium", rec.rejected)

    def test_total_volume_can_exceed_box_even_if_each_item_fits(self):
        item = make_product("Slab", 10, 10, 5, 0.1)          # 500 cm3 each
        box = make_box("Cube", 10, 10, 10, 5, 10)             # 1000 cm3, usable 850
        rec = recommend_box([(item, 2)], [box])               # 1000 > 850
        self.assertIsNone(rec.box)

    def test_volume_exactly_at_usable_limit_is_allowed(self):
        item = make_product("Snug", 10, 10, 8.5, 0.1)         # 850 cm3
        box = make_box("Cube", 10, 10, 10, 5, 10)
        rec = recommend_box([(item, 1)], [box])
        self.assertIsNotNone(rec.box)

    def test_tie_on_cost_prefers_smaller_volume(self):
        item = make_product("Cup", 5, 5, 5, 0.2)
        boxes = [make_box("Bigger", 40, 40, 40, 10, 10), make_box("Smaller", 20, 20, 20, 10, 10)]
        rec = recommend_box([(item, 1)], boxes)
        self.assertEqual(rec.box.name, "Smaller")

    def test_mixed_items_totals(self):
        a = make_product("A", 10, 10, 10, 1)
        b = make_product("B", 5, 5, 5, 0.5)
        rec = recommend_box([(a, 2), (b, 4)], [make_box("Box", 50, 50, 50, 20, 10)])
        self.assertEqual(rec.total_weight_kg, Decimal("4.0"))
        self.assertEqual(rec.total_volume_cm3, Decimal("2500"))

    def test_empty_order_raises_error(self):
        with self.assertRaises(ValueError):
            recommend_box([], [make_box("Any", 10, 10, 10, 5, 5)])

    def test_no_boxes_available(self):
        item = make_product("Thing", 5, 5, 5, 1)
        rec = recommend_box([(item, 1)], [])
        self.assertIsNone(rec.box)


class RecommendBoxApiTests(APITestCase):
    def setUp(self):
        Box.objects.create(name="Small", inner_length_cm=20, inner_width_cm=15,
                           inner_height_cm=10, max_weight_kg=2, cost=10)
        Box.objects.create(name="Medium", inner_length_cm=40, inner_width_cm=30,
                           inner_height_cm=20, max_weight_kg=10, cost=20)
        self.mug = Product.objects.create(name="Mug", length_cm=10, width_cm=10,
                                          height_cm=12, weight_kg=Decimal("0.4"))
        self.book = Product.objects.create(name="Book", length_cm=25, width_cm=18,
                                           height_cm=4, weight_kg=Decimal("0.8"))

    def test_post_recommends_box(self):
        payload = {"items": [{"product_id": self.mug.id, "quantity": 2},
                             {"product_id": self.book.id, "quantity": 1}]}
        resp = self.client.post("/api/recommend-box/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["recommended_box"]["name"], "Medium")
        self.assertIn("Small", resp.data["rejected_boxes"])

    def test_post_empty_items_returns_400(self):
        resp = self.client.post("/api/recommend-box/", {"items": []}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_post_zero_quantity_returns_400(self):
        payload = {"items": [{"product_id": self.mug.id, "quantity": 0}]}
        resp = self.client.post("/api/recommend-box/", payload, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_post_unknown_product_returns_400(self):
        payload = {"items": [{"product_id": 9999, "quantity": 1}]}
        resp = self.client.post("/api/recommend-box/", payload, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_post_no_box_fits_returns_null_box(self):
        giant = Product.objects.create(name="Giant", length_cm=300, width_cm=100,
                                       height_cm=100, weight_kg=5)
        payload = {"items": [{"product_id": giant.id, "quantity": 1}]}
        resp = self.client.post("/api/recommend-box/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data["recommended_box"])

    def test_order_endpoint_recommends_box(self):
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.mug, quantity=2)
        resp = self.client.get(f"/api/orders/{order.id}/recommend-box/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["recommended_box"]["name"], "Small")

    def test_order_not_found_returns_404(self):
        resp = self.client.get("/api/orders/9999/recommend-box/")
        self.assertEqual(resp.status_code, 404)

    def test_order_without_items_returns_400(self):
        order = Order.objects.create()
        resp = self.client.get(f"/api/orders/{order.id}/recommend-box/")
        self.assertEqual(resp.status_code, 400)