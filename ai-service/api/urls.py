from django.urls import path
from .views import (
    TrackBehaviorView,
    RecommendationView,
    ChatView,
    SearchView,
    SimilarProductsView,
    GraphVisualizationView,
)

urlpatterns = [
    path('track-behavior/', TrackBehaviorView.as_view(), name='track_behavior'),
    path('recommendations/<str:user_id>/', RecommendationView.as_view(), name='recommendation'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('search/', SearchView.as_view(), name='search'),
    # Câu 2b — KB Graph endpoints
    path('graph/products/<str:product_id>/similar/', SimilarProductsView.as_view(), name='similar_products'),
    path('graph/visualize/<str:user_id>/', GraphVisualizationView.as_view(), name='graph_visualize'),
]
