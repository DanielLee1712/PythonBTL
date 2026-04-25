"""
URL configuration for AI Service.

Endpoints:
  /                           → Health check
  /api/v1/track-behavior/     → Track user behavior
  /api/v1/recommendations/    → User recommendations (DL + FAISS)
  /api/v1/chat/               → RAG LLM Chat (KB Graph + LangChain)
  /api/v1/search/             → AI-enhanced search
  /api/ai/graph/products/     → Similar products (Collaborative Filtering)
  /api/ai/graph/visualize/    → KB Graph visualization (pyvis)
"""
from django.contrib import admin
from django.urls import path, include
from api.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    # Câu 2b/2d — AI Graph endpoints (aliased for frontend compatibility)
    path('api/ai/', include('api.urls')),
    path('', HealthCheckView.as_view(), name='health_check'),
]
