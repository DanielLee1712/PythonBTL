import os
import faiss
import numpy as np
import json
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class MLService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'index'):
            self.index = None
            self.user_embeddings = {}
            self.product_mapping = {}
            self.sentence_model = None
            self.load_models()

    def load_models(self):
        # 1. Load Sentence model for query embedding (RAG)
        logger.info("Loading SentenceTransformer model for online encoding...")
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, 'models')
        
        index_path = os.path.join(models_dir, 'product_index.faiss')
        users_path = os.path.join(models_dir, 'user_embeddings.npy')
        mapping_path = os.path.join(models_dir, 'product_mapping.json')
        
        try:
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
                logger.info("Loaded FAISS index successfully.")
                
            if os.path.exists(users_path):
                self.user_embeddings = np.load(users_path, allow_pickle=True).item()
                logger.info(f"Loaded {len(self.user_embeddings)} user embeddings.")
                
            if os.path.exists(mapping_path):
                with open(mapping_path, 'r') as f:
                    self.product_mapping = json.load(f)
                logger.info(f"Loaded {len(self.product_mapping)} product mappings.")
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")

    def search_faiss(self, user_vector, k=5):
        if self.index is None:
            return []
            
        # Ensure user_vector is 2D numpy array float32
        vector_np = np.array([user_vector]).astype('float32')
        
        # Search using L2 FAISS
        distances, indices = self.index.search(vector_np, k)
        
        # Map integer indices back to original product IDs
        recommended_ids = []
        for idx in indices[0]:
            idx_str = str(idx)
            if idx_str in self.product_mapping:
                recommended_ids.append(self.product_mapping[idx_str])
            elif idx != -1: 
                # -1 means FAISS didn't find enough matches
                pass
                
        return recommended_ids

    def encode_text(self, text):
        """Encode a single raw text string to a float32 vector array compatible with FAISS"""
        if self.sentence_model is None:
            return np.zeros(384, dtype='float32') # Fallback shape
        return self.sentence_model.encode([text])[0]

ml_service = MLService()
