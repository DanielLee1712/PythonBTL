import os
import sys

# Add ai-service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-service'))

os.environ["NEO4J_URI"] = "bolt://neo4j:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"

from api.graph_service import get_user_graph_context
from api.rag_service import _build_graph_context_text

try:
    print("Fetching graph context...")
    ctx = get_user_graph_context("1")
    print(ctx)
    print("\n--- Context Text ---")
    text, ids = _build_graph_context_text("1")
    print(text)
except Exception as e:
    print("Error:", e)
