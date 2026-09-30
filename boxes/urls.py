from django.urls import path

from .views import OrderRecommendBoxView, RecommendBoxView

urlpatterns = [
    path("recommend-box/", RecommendBoxView.as_view(), name="recommend-box"),
    path("orders/<int:order_id>/recommend-box/", OrderRecommendBoxView.as_view(), name="order-recommend-box"),
]