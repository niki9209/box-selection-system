from rest_framework import serializers

from .models import Product


class ItemInputSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product"
    )
    quantity = serializers.IntegerField(min_value=1)


class RecommendRequestSerializer(serializers.Serializer):
    items = ItemInputSerializer(many=True, allow_empty=False)


def recommendation_payload(rec):
    box = rec.box
    return {
        "recommended_box": None if box is None else {
            "id": box.id,
            "name": box.name,
            "cost": str(box.cost),
        },
        "message": rec.message,
        "total_weight_kg": str(rec.total_weight_kg),
        "total_volume_cm3": str(rec.total_volume_cm3),
        "rejected_boxes": rec.rejected,
    }