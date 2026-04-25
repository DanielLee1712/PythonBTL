import os
import sys
import numpy as np
import pandas as pd
import psycopg2
import faiss
from sentence_transformers import SentenceTransformer
import logging
import json

# Add parent directory to path so we can import api modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.neo4j_client import neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config DB Products
DB_HOST = os.environ.get("PRODUCT_DB_HOST", "localhost")
DB_PORT = os.environ.get("PRODUCT_DB_PORT", "5434")
DB_NAME = os.environ.get("PRODUCT_DB_NAME", "product_db")
DB_USER = os.environ.get("PRODUCT_DB_USER", "shop_user")
DB_PASS = os.environ.get("PRODUCT_DB_PASS", "shop_password")

def get_products():
    """Fetch product data from Postgres"""
    logger.info("Connecting to Product DB...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    # the table name depends on django model apps, likely catalog_product
    query = "SELECT id, title, description FROM catalog_product"
    try:
        df = pd.read_sql(query, conn)
    except psycopg2.errors.UndefinedTable:
        # fallback if name differs
        logger.error("Could not find table 'catalog_product'. Trying 'product'")
        df = pd.read_sql("SELECT id, title, description FROM product", conn)
    finally:
        conn.close()
    return df

def get_user_interactions():
    """Fetch user interactions from Neo4j Grapg"""
    logger.info("Fetching interactions from Neo4j...")
    query = """
    MATCH (u:User)-[r:INTERACTS_WITH]->(p:Product)
    RETURN u.id as user_id, collect(p.id) as product_ids
    """
    neo4j_client.connect()
    # Force credentials override for local script if NEO4J_URI isn't exported appropriately
    # The client uses Env variables. We assume the environment is set properly locally or via docker.
    result = neo4j_client.execute_read(query)
    
    user_data = {}
    if result:
        for record in result:
            user_data[record['user_id']] = record['product_ids']
    return user_data

def main():
    logger.info("Step 1: Fetching products...")
    try:
        products_df = get_products()
    except Exception as e:
         logger.error(f"Failed to load products: {e}")
         logger.info("Fallback: using generated dummy names if db is empty or inaccessible for testing purposes.")
         products_df = pd.DataFrame([
             {"id": str(i), "title": f"Product {i}", "description": f"This is product {i} description"} for i in range(1, 101)
         ])
         
    if len(products_df) == 0:
         logger.warning("DB Connected but no products found!")
         return

    logger.info(f"Loaded {len(products_df)} products. Generating texts...")
    products_df['text_content'] = products_df['title'] + " " + products_df['description'].fillna('')
    product_texts = products_df['text_content'].tolist()
    product_ids = products_df['id'].astype(str).tolist()

    logger.info("Step 2: Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    logger.info("Step 3: Generating embeddings...")
    embeddings = model.encode(product_texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    dimension = embeddings.shape[1] # should be 384
    logger.info(f"Embeddings shape: {embeddings.shape}")
    
    logger.info("Step 4: Building FAISS Index...")
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save product mappings
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    faiss.write_index(index, os.path.join(models_dir, 'product_index.faiss'))
    
    # Save mapping from FAISS integer index -> product UUID/ID string
    id_mapping = {i: pid for i, pid in enumerate(product_ids)}
    with open(os.path.join(models_dir, 'product_mapping.json'), 'w') as f:
        json.dump(id_mapping, f)
        
    logger.info("Saved product_index.faiss and product_mapping.json")
    
    logger.info("Step 5: Generating User Centroid Embeddings...")
    user_interactions = get_user_interactions()
    
    # map product string ID to integer FAISS index for quick lookup
    inv_id_mapping = {pid: i for i, pid in id_mapping.items()}
    
    user_embeddings = {}
    
    for user_id, p_ids in user_interactions.items():
        # Get vectors for interacted products
        p_indices = [inv_id_mapping[pid] for pid in p_ids if pid in inv_id_mapping]
        if not p_indices:
            continue
            
        interacted_vectors = embeddings[p_indices]
        # Calculate centroid (mean vector)
        user_vector = np.mean(interacted_vectors, axis=0)
        user_embeddings[str(user_id)] = user_vector
        
    logger.info(f"Generated embeddings for {len(user_embeddings)} users")
    np.save(os.path.join(models_dir, 'user_embeddings.npy'), user_embeddings)
    
    logger.info("Completed successfully!")

if __name__ == '__main__':
    # Add psycopg2 warning suppression about pandas sqlalchemy
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    main()
