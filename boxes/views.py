from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Box, Order
from .serializers import RecommendRequestSerializer, recommendation_payload
from .services import recommend_box, recommend_box_for_order


class RecommendBoxView(APIView):
    def post(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = [(i["product"], i["quantity"]) for i in serializer.validated_data["items"]]
        rec = recommend_box(items, Box.objects.all())
        return Response(recommendation_payload(rec))


class OrderRecommendBoxView(APIView):
    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        if not order.items.exists():
            return Response(
                {"detail": "Order has no items."}, status=status.HTTP_400_BAD_REQUEST
            )
        rec = recommend_box_for_order(order)
        return Response(recommendation_payload(rec))