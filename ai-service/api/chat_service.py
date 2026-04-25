import os
import psycopg2
import logging
from .ml_service import ml_service
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

try:
    from groq import Groq  # type: ignore
except Exception as e:
    Groq = None
    logger.warning("Groq SDK not available (%s). Chat will run in fallback mode.", e)

groq_api_key = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=groq_api_key) if (Groq and groq_api_key) else None

DB_HOST = os.environ.get("PRODUCT_DB_HOST", "localhost")
DB_PORT = os.environ.get("PRODUCT_DB_PORT", "5434")
DB_NAME = os.environ.get("PRODUCT_DB_NAME", "product_db")
DB_USER = os.environ.get("PRODUCT_DB_USER", "shop_user")
DB_PASS = os.environ.get("PRODUCT_DB_PASS", "shop_password")

def get_product_details_from_db(product_ids):
    if not product_ids:
        return []
    
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS
        )
        cur = conn.cursor()
        format_strings = ','.join(['%s'] * len(product_ids))
        
        try:
            cur.execute(f"SELECT id, title FROM catalog_product WHERE id IN ({format_strings})", tuple(product_ids))
            rows = cur.fetchall()
        except Exception:
            conn.rollback()
            cur.execute(f"SELECT id, title FROM product WHERE id IN ({format_strings})", tuple(product_ids))
            rows = cur.fetchall()
            
        cur.close()
        return [{"id": row[0], "name": row[1]} for row in rows]
    except Exception as e:
        logger.error(f"Postgres error: {e}")
        return [{"id": pid, "name": f"Sản phẩm {pid}"} for pid in product_ids]
    finally:
        if conn:
            conn.close()

def get_user_recent_views(user_id):
    query = """
    MATCH (u:User {id: $user_id})-[r:INTERACTS_WITH]->(p:Product)
    RETURN p.id as product_id
    LIMIT 3
    """
    records = neo4j_client.execute_read(query, {'user_id': str(user_id)})
    if not records:
        return []
    
    p_ids = [rec['product_id'] for rec in records]
    return get_product_details_from_db(p_ids)

def generate_graphrag_response(user_id, user_message, message_vector):
    # 1. FAISS Semantic Search
    faiss_product_ids = ml_service.search_faiss(message_vector, k=3)
    
    # 2. Query Postgres
    products = get_product_details_from_db(faiss_product_ids)
    matched_products_text = "\n".join([f"- ID: {p['id']} | Tên: {p['name']}" for p in products])
    
    # 3. Query Neo4j User History
    user_history_products = get_user_recent_views(user_id)
    history_text = ", ".join([p['name'] for p in user_history_products]) if user_history_products else "Khách mới, chưa có lịch sử."
    
    # 4. Prompt
    system_prompt = f"""
    Bạn là AI tư vấn bán hàng E-commerce tận tâm, ngắn gọn và thân thiện.
    
    [SỞ THÍCH KHÁCH HÀNG TỪ GRAPH DB]
    Khách từng quan tâm các món: {history_text}
    
    [SẢN PHẨM PHÙ HỢP TRONG KHO TỪ VECTOR DB]
    {matched_products_text}
    
    Nhiệm vụ: Dựa vào sở thích, hãy tư vấn cho khách chọn 1 trong các sản phẩm trên. Không bịa thêm sản phẩm ngoài danh sách. Trả lời bằng tiếng Việt.
    """
    
    # 5. Call Groq
    if not client:
        return {
            "reply": "Hệ thống chưa sẵn sàng gọi Groq (thiếu GROQ_API_KEY hoặc chưa cài Groq SDK). Vui lòng cấu hình file .env của AI-Service và rebuild container.",
            "suggestedProductIds": faiss_product_ids
        }

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.5,
            max_tokens=256,
        )
        reply = chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        reply = f"Xin lỗi, hiện tại tôi bị lỗi kết nối với LLM: {str(e)}"

    return {
        "reply": reply,
        "suggestedProductIds": faiss_product_ids
    }
