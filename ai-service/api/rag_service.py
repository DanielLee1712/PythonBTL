"""
Câu 2c — RAG LLM & Chat Service

LangChain-based RAG pipeline:
  - Primary Retriever: KB Graph (Neo4j) — user history + Collaborative Filtering
  - Supplementary Retriever: Product Catalog Search — keyword-based product lookup
  - Generator: Groq (Llama 3.1) / Ollama (llama3.2) via LangChain

Pipeline:
  1. [KB_Graph] Query Neo4j for user context (purchases, interactions, CF recommendations)
  2. [Catalog]  Search Product DB by keywords extracted from user message (supplementary)
  3. Enrich product IDs with real names from Product Service
  4. Fuse both contexts into a single prompt
  5. Call LLM via LangChain
"""
from __future__ import annotations
import logging, os
import psycopg2
from typing import Any, Dict, List

from .graph_service import get_user_graph_context

logger = logging.getLogger(__name__)

# ── Product DB Config ──
DB_HOST = os.environ.get("PRODUCT_DB_HOST", "localhost")
DB_PORT = os.environ.get("PRODUCT_DB_PORT", "5434")
DB_NAME = os.environ.get("PRODUCT_DB_NAME", "product_db")
DB_USER = os.environ.get("PRODUCT_DB_USER", "shop_user")
DB_PASS = os.environ.get("PRODUCT_DB_PASS", "shop_password")

# ── LLM Config ──
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Initialize LangChain LLM ──
_llm = None
_llm_provider = "none"


def _init_llm():
    """Lazy-init LLM: try Groq first, fallback to Ollama, then None."""
    global _llm, _llm_provider

    if _llm is not None:
        return

    # 1. Try Groq (primary)
    if GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            _llm = ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=GROQ_API_KEY,
                temperature=0.1,
                max_tokens=512,
            )
            _llm_provider = "groq"
            logger.info("RAG LLM initialized: Groq (llama-3.1-8b-instant)")
            return
        except Exception as e:
            logger.warning("Failed to init Groq LLM: %s", e)

    # 2. Fallback: Ollama Local
    try:
        from langchain_community.llms import Ollama
        _llm = Ollama(model="llama3.2", base_url=OLLAMA_BASE_URL, temperature=0.1)
        _llm_provider = "ollama"
        logger.info("RAG LLM initialized: Ollama Local (llama3.2)")
        return
    except Exception as e:
        logger.warning("Failed to init Ollama LLM: %s", e)

    logger.error("No LLM available. RAG chat will return fallback messages.")


import urllib.request
import urllib.parse
import json


# ═══════════════════════════════════════════════════════════
# RETRIEVER 1: Product Service API (shared helper)
# ═══════════════════════════════════════════════════════════

def _get_product_details(product_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetch product names from Product Service API."""
    if not product_ids:
        return []
    try:
        product_service_url = os.environ.get("PRODUCT_SERVICE_PRODUCTS_URL", "http://product-service:8001/api/v1/products/")
        url = f"{product_service_url}?ids={','.join(map(str, product_ids))}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            raw = resp.read().decode("utf-8")
        payload = json.loads(raw)
        results = payload.get("results", payload)
        if isinstance(results, list):
            return [{"id": str(p.get("id")), "name": p.get("title", p.get("name", f"Product {p.get('id')}"))} for p in results]
    except Exception as e:
        logger.error("API lookup error for product names: %s", e)
    
    return [{"id": pid, "name": f"Product {pid}"} for pid in product_ids]


# ═══════════════════════════════════════════════════════════
# RETRIEVER 2 (PRIMARY): KB Graph — Neo4j user context + CF
# ═══════════════════════════════════════════════════════════

def _build_graph_context_text(user_id: str) -> tuple[str, List[str]]:
    """Build context text from KB Graph for the RAG prompt."""
    ctx = get_user_graph_context(str(user_id), limit=10)

    # Enrich product IDs with names
    all_pids = list(set(
        [i["product_id"] for i in ctx["interactions"]] +
        [p["product_id"] for p in ctx["purchases"]] +
        [r["product_id"] for r in ctx["cf_recommendations"]]
    ))
    products = _get_product_details(all_pids)
    pid_to_name = {str(p["id"]): p["name"] for p in products}

    # Filter function to only keep valid product names
    def get_valid_name(pid):
        name = pid_to_name.get(str(pid))
        if not name or name == str(pid) or name.startswith("Product "):
            return None
        return name

    # Build text sections
    sections = []

    if ctx["purchases"]:
        items = []
        for p in ctx["purchases"][:10]:
            name = get_valid_name(p['product_id'])
            if name:
                items.append(f"  - {name}")
        if items:
            sections.append("SẢN PHẨM KHÁCH ĐÃ MUA TRƯỚC ĐÂY:\n" + "\n".join(items[:5]))
    elif ctx["interactions"]:
        items = []
        for i in ctx["interactions"][:15]:
            name = get_valid_name(i['product_id'])
            if name:
                items.append(f"  - {name}")
        if items:
            sections.append("SẢN PHẨM KHÁCH ĐÃ TÌM HIỂU/QUAN TÂM:\n" + "\n".join(items[:8]))

    if ctx["cf_recommendations"]:
        items = []
        for r in ctx["cf_recommendations"][:15]:
            name = get_valid_name(r['product_id'])
            if name:
                items.append(f"  - {name}")
        if items:
            sections.append("GỢI Ý TỪ KHÁCH HÀNG TƯƠNG TỰ:\n" + "\n".join(items[:5]))

    context_text = "\n\n".join(sections) if sections else "Khách mới, chưa có lịch sử mua sắm."

    suggested_ids = [i["product_id"] for i in ctx["interactions"][:5]]
    if ctx["cf_recommendations"]:
        suggested_ids += [r["product_id"] for r in ctx["cf_recommendations"]]

    return context_text, suggested_ids[:10]


# ═══════════════════════════════════════════════════════════
# RETRIEVER 3 (SUPPLEMENTARY): Product Catalog Search
# ═══════════════════════════════════════════════════════════

def _search_product_catalog(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Search product catalog by keyword.
    
    This is the supplementary retriever: when KB_Graph doesn't have
    relevant products for the user's question (e.g. asking about laptops
    when history is all cosmetics), this retriever fills the gap by
    searching the actual product database.
    """
    if not query or len(query.strip()) < 2:
        return []
    try:
        product_service_url = os.environ.get(
            "PRODUCT_SERVICE_PRODUCTS_URL",
            "http://product-service:8001/api/v1/products/"
        )
        params = {"search": query.strip(), "page_size": k}
        url = f"{product_service_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            raw = resp.read().decode("utf-8")
        payload = json.loads(raw)
        results = payload.get("results", payload)
        if isinstance(results, list):
            return [
                {
                    "name": p.get("title", p.get("name", "")),
                    "price": p.get("price", 0),
                    "category": p.get("category_name", ""),
                }
                for p in results
                if p.get("title") or p.get("name")
            ]
    except Exception as e:
        logger.error("Product catalog search failed for '%s': %s", query, e)
    return []


def _extract_search_keywords(message: str) -> str:
    """Extract product-related keywords from user message for catalog search."""
    category_keywords = [
        # Electronics
        "laptop", "điện thoại", "phone", "tai nghe", "headphone",
        "bàn phím", "keyboard", "chuột", "mouse", "màn hình", "monitor",
        "tivi", "tv", "máy tính", "pc", "gaming", "camera", "iphone",
        "samsung", "xiaomi", "oppo", "macbook",
        # Cosmetics
        "son", "kem nền", "phấn", "mascara", "lipstick", "foundation",
        "trang điểm", "makeup", "mỹ phẩm", "skincare", "serum",
        # Fashion
        "áo", "quần", "váy", "giày", "dép", "túi xách",
        "thời trang", "fashion", "đồng hồ", "watch", "nike", "adidas", "puma",
        # Home appliances
        "tủ lạnh", "máy giặt", "điều hòa", "nồi", "bếp",
        # Other
        "sách", "book",
    ]
    
    msg_lower = message.lower()
    found = [kw for kw in category_keywords if kw in msg_lower]
    
    if found:
        return max(found, key=len)  # Return most specific keyword
    return ""


def _format_price(price) -> str:
    """Format price to Vietnamese currency string."""
    try:
        p = int(float(price))
        if p <= 0:
            return ""
        return f"{p:,}".replace(",", ".") + " ₫"
    except (ValueError, TypeError):
        return ""


# ═══════════════════════════════════════════════════════════
# MAIN RAG PIPELINE
# ═══════════════════════════════════════════════════════════

def generate_response(user_id: str | None, user_message: str) -> Dict[str, Any]:
    """
    Main RAG pipeline:
    1. [Primary]       Retrieve context from KB Graph (Neo4j) — history + CF
    2. [Supplementary] Search product catalog by keywords from user message
    3. Fuse contexts and build prompt
    4. Call LLM via LangChain
    """
    _init_llm()

    # ── Step 1: Primary Retriever — KB Graph ──
    if user_id:
        graph_context, suggested_ids = _build_graph_context_text(str(user_id))
    else:
        graph_context = "Khách mới, chưa có lịch sử mua sắm."
        suggested_ids = []

    # ── Step 2: Supplementary Retriever — Product Catalog Search ──
    catalog_section = ""
    search_keyword = _extract_search_keywords(user_message)
    if search_keyword:
        catalog_results = _search_product_catalog(search_keyword, k=5)
        if catalog_results:
            items = []
            for p in catalog_results:
                price_str = _format_price(p["price"])
                name = p["name"]
                if price_str:
                    items.append(f"  - {name} — {price_str}")
                else:
                    items.append(f"  - {name}")
            catalog_section = "SẢN PHẨM ĐANG BÁN TẠI CỬA HÀNG (tìm theo yêu cầu):\n" + "\n".join(items)

    # ── Step 3: Fuse contexts ──
    full_context = graph_context
    if catalog_section:
        full_context += "\n\n" + catalog_section

    # ── Step 4: Build prompt ──
    system_prompt = f"""Bạn là một nhân viên tư vấn bán hàng chuyên nghiệp, thân thiện, nói chuyện tự nhiên.

[DỮ LIỆU KHÁCH HÀNG]
{full_context}

CÁCH TƯ VẤN:
- Trả lời ngắn gọn (2-3 câu), tự nhiên như người bán hàng thật.
- KHÔNG BAO GIỜ nhắc: "Collaborative Filtering", "ID", "Knowledge Graph", "danh sách gợi ý", "hệ thống", "dữ liệu", "hồ sơ", "catalog", "cửa hàng tìm theo yêu cầu".

CÁCH SỬ DỤNG DỮ LIỆU:
- Chỉ nhắc lịch sử mua hàng KHI khách chủ động đề cập ("hôm trước tôi mua..."). Lúc đó nhắc đúng tên sản phẩm.
- KHÔNG TỰ TIỆN lôi lịch sử ra nếu khách hỏi về danh mục khác (hỏi laptop thì KHÔNG nhắc son MAC).
- ƯU TIÊN gợi ý sản phẩm từ "GỢI Ý TỪ KHÁCH HÀNG TƯƠNG TỰ" nếu có sản phẩm ĐÚNG danh mục khách hỏi.
- Nếu gợi ý từ Graph không liên quan, hãy dùng "SẢN PHẨM ĐANG BÁN TẠI CỬA HÀNG" để tư vấn kèm giá.
- Nếu cả hai nguồn đều không có → tư vấn chung, mời khách dùng thanh Tìm kiếm.
- TUYỆT ĐỐI KHÔNG bịa ra tên sản phẩm không có trong dữ liệu trên."""

    # ── Step 5: Call LLM ──
    if _llm is None:
        return {
            "reply": "Hệ thống AI chưa sẵn sàng. Vui lòng cấu hình GROQ_API_KEY hoặc Ollama.",
            "provider": "none",
        }

    try:
        if _llm_provider == "groq":
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
            response = _llm.invoke(messages)
            reply = response.content
        else:
            # Ollama (non-chat model)
            full_prompt = f"{system_prompt}\n\nKhách hàng: {user_message}\n\nTư vấn viên:"
            reply = _llm.invoke(full_prompt)
    except Exception as e:
        logger.error("LLM call failed (%s): %s", _llm_provider, e)
        reply = f"Xin lỗi, hiện tại tôi gặp lỗi kết nối LLM ({_llm_provider}): {str(e)}"

    return {
        "reply": reply,
        "provider": _llm_provider,
    }
