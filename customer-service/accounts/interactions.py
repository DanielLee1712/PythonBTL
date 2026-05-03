from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser, WishlistItem, ProductRating


class WishlistListView(APIView):
    """
    MVP wishlist API (dev): use user_id from query/body.
    GET  /api/interactions/wishlist/?user_id=1
    POST /api/interactions/wishlist/ {user_id, product_id}
    """

    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"detail": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        items = WishlistItem.objects.filter(user_id=int(user_id)).values_list("product_id", flat=True)
        return Response({"user_id": int(user_id), "product_ids": list(items)})

    def post(self, request):
        user_id = request.data.get("user_id")
        product_id = request.data.get("product_id")
        if user_id is None or product_id is None:
            return Response({"detail": "user_id and product_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        user = CustomUser.objects.filter(id=int(user_id)).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        WishlistItem.objects.get_or_create(user=user, product_id=int(product_id))
        return Response({"ok": True}, status=status.HTTP_200_OK)


class WishlistItemView(APIView):
    """
    DELETE /api/interactions/wishlist/<product_id>/?user_id=1
    """

    def delete(self, request, product_id: int):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"detail": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        WishlistItem.objects.filter(user_id=int(user_id), product_id=int(product_id)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RatingView(APIView):
    """
    MVP rating API (dev):
    GET  /api/interactions/ratings/?user_id=1&product_id=50
    POST /api/interactions/ratings/ {user_id, product_id, rating(1..5)}
    Returns: user_rating, avg_rating, rating_count
    """

    def get(self, request):
        user_id = request.query_params.get("user_id")
        product_id = request.query_params.get("product_id")
        if not user_id or not product_id:
            return Response({"detail": "user_id and product_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        uid = int(user_id)
        pid = int(product_id)

        ur = ProductRating.objects.filter(user_id=uid, product_id=pid).first()
        wish_cnt = WishlistItem.objects.filter(product_id=pid).count()
        agg = ProductRating.objects.filter(product_id=pid).aggregate(
            avg=Avg("rating"),
            cnt=Count("id"),
        )
        return Response(
            {
                "user_id": uid,
                "product_id": pid,
                "user_rating": ur.rating if ur else None,
                "avg_rating": float(agg["avg"]) if agg["avg"] is not None else None,
                "rating_count": int(agg["cnt"] or 0),
                "wishlist_count": int(wish_cnt),
            }
        )

    def post(self, request):
        user_id = request.data.get("user_id")
        product_id = request.data.get("product_id")
        rating = request.data.get("rating")
        if user_id is None or product_id is None or rating is None:
            return Response(
                {"detail": "user_id, product_id, rating are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        uid = int(user_id)
        pid = int(product_id)
        r = int(rating)
        if r < 1 or r > 5:
            return Response({"detail": "rating must be 1..5"}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.filter(id=uid).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        obj, _ = ProductRating.objects.update_or_create(
            user=user,
            product_id=pid,
            defaults={"rating": r},
        )

        wish_cnt = WishlistItem.objects.filter(product_id=pid).count()
        agg = ProductRating.objects.filter(product_id=pid).aggregate(
            avg=Avg("rating"),
            cnt=Count("id"),
        )
        return Response(
            {
                "user_id": uid,
                "product_id": pid,
                "user_rating": obj.rating,
                "avg_rating": float(agg["avg"]) if agg["avg"] is not None else None,
                "rating_count": int(agg["cnt"] or 0),
                "wishlist_count": int(wish_cnt),
            },
            status=status.HTTP_200_OK,
        )

