from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .neo4j_client import neo4j_client
from .kb_graph import action_weight, clean_identifier, normalize_action
from .ml_service import ml_service
from .rag_service import generate_response
from .sequence_service import sequence_service
from .graph_service import get_similar_products, render_pyvis_html
import logging
from datetime import datetime
import os
import json
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


class TrackBehaviorView(APIView):
    def post(self, request):
        data = request.data
        user_id = clean_identifier(data.get('user_id'))
        product_id = clean_identifier(data.get('product_id'))
        action = normalize_action(data.get('action') or data.get('behavior_type'))
        event_time = datetime.utcnow().replace(microsecond=0).isoformat()

        if not all([user_id, product_id, action]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        query = """
        MERGE (u:User {id: $user_id})
        MERGE (p:Product {id: $product_id})
        MERGE (u)-[r:INTERACTS_WITH {action: $action}]->(p)
        ON CREATE SET
            r.count = 1,
            r.first_ts = $event_ts,
            r.last_ts = $event_ts,
            r.weight = $action_weight
        ON MATCH SET
            r.count = r.count + 1,
            r.last_ts = $event_ts,
            r.weight = r.weight + $action_weight
        """
        params = {
            'user_id': str(user_id),
            'product_id': str(product_id),
            'action': action,
            'event_ts': event_time,
            'action_weight': float(action_weight(action)),
        }
        neo4j_client.execute_write(query, params)
        
        return Response({'status': 'Behavior tracked successfully'}, status=status.HTTP_201_CREATED)


class RecommendationView(APIView):
    def get(self, request, user_id):
        # 1) DL ensemble → sequence model → FAISS fallback
        recommendations = sequence_service.recommend_next_items(str(user_id), k=5)

        # 2) Fallback: vector similarity (FAISS) from precomputed user embedding
        if not recommendations:
            user_vector = ml_service.user_embeddings.get(str(user_id))
            if user_vector is not None:
                recommendations = ml_service.search_faiss(user_vector, k=5)
            else:
                recommendations = []
            
        return Response({'user_id': user_id, 'recommendations': recommendations}, status=status.HTTP_200_OK)


class ChatView(APIView):
    """Câu 2c — RAG LLM Chat using KB Graph context + LangChain."""
    def post(self, request):
        user_message = request.data.get('message', '')
        user_id = request.data.get('user_id')
        
        logger.info(f"Received chat from {user_id}: {user_message}")
        
        if not user_message:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # RAG pipeline: KB Graph → LangChain → Groq/Ollama
            result = generate_response(user_id, user_message)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Chat API error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchView(APIView):
    def post(self, request):
        data = request.data or {}
        query = str(data.get("query", "")).strip()
        user_id = data.get("user_id")
        k = int(data.get("k", 20) or 20)

        if not query:
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

        product_service_url = os.environ.get("PRODUCT_SERVICE_PRODUCTS_URL", "http://localhost:8001/api/v1/products/")
        params = {"search": query, "page_size": 50}
        url = f"{product_service_url}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                raw = resp.read().decode("utf-8")
            payload = json.loads(raw)
            candidates = payload.get("results", payload)
            if not isinstance(candidates, list):
                candidates = []
        except Exception as e:
            logger.error("Product-service search failed: %s", e)
            candidates = []

        # Rerank candidates using sequence next-item probabilities.
        if user_id is not None:
            scores = sequence_service.predict_next_scores(str(user_id), top_k=500)
            if scores:
                def score_of(prod: dict) -> float:
                    pid = str(prod.get("id", ""))
                    return float(scores.get(pid, 0.0))

                candidates = sorted(candidates, key=score_of, reverse=True)

        return Response(
            {
                "query": query,
                "user_id": user_id,
                "results": candidates[:k],
            },
            status=status.HTTP_200_OK,
        )


class SimilarProductsView(APIView):
    """Câu 2b — GET /api/ai/graph/products/{id}/similar
    Collaborative Filtering via KB Graph.
    """
    def get(self, request, product_id):
        k = int(request.query_params.get("k", 5))
        results = get_similar_products(str(product_id), k=k)
        return Response({
            "product_id": product_id,
            "similar_products": results,
        }, status=status.HTTP_200_OK)


class GraphVisualizationView(APIView):
    """Câu 2b — GET /api/ai/graph/visualize/{user_id}/
    Interactive pyvis HTML visualization of user's KB Graph.
    """
    def get(self, request, user_id):
        from django.http import HttpResponse
        html = render_pyvis_html(str(user_id), max_edges=50)
        return HttpResponse(html, content_type="text/html")


class HealthCheckView(APIView):
    def get(self, request):
        return Response({'status': 'AI Service is running'}, status=status.HTTP_200_OK)
