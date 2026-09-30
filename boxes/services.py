from dataclasses import dataclass, field
from decimal import Decimal

# Usable fraction of a box's volume. Real items never pack perfectly,
# so we only allow items to fill this share of the box.
FILL_FACTOR = Decimal("0.85")


@dataclass
class Recommendation:
    box: object | None            # the chosen Box, or None if nothing fits
    total_weight_kg: Decimal
    total_volume_cm3: Decimal
    message: str
    rejected: dict = field(default_factory=dict)   # box name -> reason


def item_fits_in_box(product, box):
    """True if the product fits inside the box in some orientation.

    Sorting both sets of dimensions and comparing smallest-to-smallest
    covers every 90-degree rotation.
    """
    return all(
        item_dim <= box_dim
        for item_dim, box_dim in zip(sorted(product.dimensions), sorted(box.dimensions))
    )


def rejection_reason(items, box, total_weight, total_volume):
    """Return why a box is unsuitable, or None if it is valid."""
    if total_weight > box.max_weight_kg:
        return "total weight exceeds box capacity"
    for product, _quantity in items:
        if not item_fits_in_box(product, box):
            return f"'{product.name}' does not fit in any orientation"
    if total_volume > box.volume * FILL_FACTOR:
        return "total volume exceeds usable box volume"
    return None


def recommend_box(items, boxes):
    """Recommend the cheapest valid box.

    items: list of (product, quantity) tuples
    boxes: iterable of Box objects
    """
    items = list(items)
    if not items:
        raise ValueError("Order has no items.")

    total_weight = sum(p.weight_kg * q for p, q in items)
    total_volume = sum(p.volume * q for p, q in items)

    valid, rejected = [], {}
    for box in boxes:
        reason = rejection_reason(items, box, total_weight, total_volume)
        if reason:
            rejected[box.name] = reason
        else:
            valid.append(box)

    if not valid:
        return Recommendation(
            box=None,
            total_weight_kg=total_weight,
            total_volume_cm3=total_volume,
            message="No single box fits this order. Consider splitting it.",
            rejected=rejected,
        )

    # Cheapest first; ties broken by smaller volume, then name (deterministic).
    best = min(valid, key=lambda b: (b.cost, b.volume, b.name))
    return Recommendation(
        box=best,
        total_weight_kg=total_weight,
        total_volume_cm3=total_volume,
        message=f"Recommended box: {best.name}",
        rejected=rejected,
    )


def recommend_box_for_order(order):
    """Thin wrapper that loads data from the database."""
    from .models import Box

    items = [(item.product, item.quantity) for item in order.items.select_related("product")]
    return recommend_box(items, Box.objects.all())