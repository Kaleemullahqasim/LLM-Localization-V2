import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from ..models import Rule
from ..config import config
from .lm_studio_client import LMStudioClient

class EmbeddingService:
    """Service for handling rule embeddings and retrieval"""
    
    def __init__(self, kb_version: str = None, locale: str = None):
        self.lm_client = LMStudioClient()
        self.embeddings_cache = {}
        self.rule_index = {}
        self.kb_version = kb_version
        self.locale = locale
        
    async def index_rules(self, rules: List[Rule], kb_version: str = None, locale: str = None):
        """Create embeddings for all rules and build search index"""
        print(f"Creating embeddings for {len(rules)} rules...")
        
        # Store version info for this index
        if kb_version:
            self.kb_version = kb_version
        if locale:
            self.locale = locale
        
        # Prepare texts for embedding (rule text + examples)
        texts = []
        rule_ids = []
        
        for rule in rules:
            # Combine rule text with examples for better retrieval
            text = rule.rule_text
            if rule.examples_pos:
                text += " Examples: " + " ".join(rule.examples_pos)
            if rule.examples_neg:
                text += " Avoid: " + " ".join(rule.examples_neg)
            
            texts.append(text)
            rule_ids.append(rule.rule_id)
        
        # Get embeddings from LM Studio
        try:
            embeddings = await self.lm_client.get_embeddings(texts)
            
            # Store in index
            for rule_id, embedding, rule in zip(rule_ids, embeddings, rules):
                self.rule_index[rule_id] = {
                    'embedding': embedding,
                    'rule': rule,
                    'text': texts[rule_ids.index(rule_id)]
                }
            
            print(f"Successfully indexed {len(embeddings)} rules")
            
            # Save index to disk
            await self._save_index()
            
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            raise
    
    async def hybrid_search(self, query_text: str, top_k: int = 10, locale: str = None, kb_version: str = None) -> List[Dict[str, Any]]:
        """Perform hybrid search: embeddings + keyword matching"""
        
        if not self.rule_index:
            await self._load_index(kb_version=kb_version, locale=locale)
        
        if not self.rule_index:
            print(f"No rule index found for kb_version={kb_version}, locale={locale}")
            return []
        
        # Get query embedding
        try:
            query_embeddings = await self.lm_client.get_embeddings([query_text])
            query_embedding = query_embeddings[0]
        except Exception as e:
            print(f"Error getting query embedding: {e}")
            return []
        
        # Calculate similarities
        similarities = []
        
        for rule_id, rule_data in self.rule_index.items():
            rule = rule_data['rule']
            
            # Skip if locale doesn't match (for multi-locale support later)
            if locale and hasattr(rule.citation, 'locale') and rule.citation.locale != locale:
                continue
            
            # Semantic similarity (embedding-based)
            rule_embedding = np.array(rule_data['embedding'])
            query_emb = np.array(query_embedding)
            
            semantic_sim = cosine_similarity(
                query_emb.reshape(1, -1), 
                rule_embedding.reshape(1, -1)
            )[0][0]
            
            # Keyword similarity (simple keyword matching)
            query_words = set(query_text.lower().split())
            rule_words = set(rule_data['text'].lower().split())
            keyword_sim = len(query_words & rule_words) / max(len(query_words), 1)
            
            # Combined score (weighted)
            combined_score = 0.7 * semantic_sim + 0.3 * keyword_sim
            
            similarities.append({
                'rule_id': rule_id,
                'rule': rule,
                'score': combined_score,
                'semantic_score': semantic_sim,
                'keyword_score': keyword_sim
            })
        
        # Sort by combined score and return top k
        similarities.sort(key=lambda x: x['score'], reverse=True)
        return similarities[:top_k]
    
    async def get_rules_by_macro_class(self, macro_class: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Get rules filtered by macro class"""
        
        if not self.rule_index:
            await self._load_index()
        
        filtered_rules = []
        for rule_id, rule_data in self.rule_index.items():
            rule = rule_data['rule']
            if rule.macro_class.value == macro_class:
                filtered_rules.append({
                    'rule_id': rule_id,
                    'rule': rule,
                    'score': 1.0  # Perfect match for class filter
                })
        
        return filtered_rules[:top_k]
    
    async def _save_index(self):
        """Save embedding index to disk"""
        index_dir = os.path.join(config.DATA_DIR, "embeddings")
        os.makedirs(index_dir, exist_ok=True)
        
        # Prepare data for serialization
        serializable_index = {}
        for rule_id, rule_data in self.rule_index.items():
            serializable_index[rule_id] = {
                'embedding': rule_data['embedding'],
                'text': rule_data['text'],
                'rule': rule_data['rule'].model_dump()
            }
        
        # Use KB-specific filename to avoid overwriting
        if self.kb_version and self.locale:
            index_file = os.path.join(index_dir, f"rule_index_{self.kb_version}_{self.locale}.json")
        else:
            index_file = os.path.join(index_dir, "rule_index_default.json")
            
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_index, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Embedding index saved: {index_file}")
    
    async def _load_index(self, kb_version: str = None, locale: str = None):
        """Load embedding index from disk"""
        index_dir = os.path.join(config.DATA_DIR, "embeddings")
        
        # Use KB-specific filename
        kb_ver = kb_version or self.kb_version
        loc = locale or self.locale
        
        if kb_ver and loc:
            index_file = os.path.join(index_dir, f"rule_index_{kb_ver}_{loc}.json")
        else:
            index_file = os.path.join(index_dir, "rule_index_default.json")
        
        if not os.path.exists(index_file):
            print(f"No saved embedding index found at {index_file}")
            return
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                serializable_index = json.load(f)
            
            # Reconstruct rule index
            from ..models import Rule, MacroClass, Severity, Citation
            from datetime import datetime
            
            for rule_id, rule_data in serializable_index.items():
                rule_dict = rule_data['rule']
                
                # Convert string values back to proper types
                if isinstance(rule_dict.get('created_at'), str):
                    rule_dict['created_at'] = datetime.fromisoformat(rule_dict['created_at'].replace('Z', '+00:00'))
                
                if isinstance(rule_dict.get('macro_class'), str):
                    rule_dict['macro_class'] = MacroClass(rule_dict['macro_class'])
                
                if isinstance(rule_dict.get('default_severity'), str):
                    rule_dict['default_severity'] = Severity(rule_dict['default_severity'])
                
                if isinstance(rule_dict.get('citation'), dict):
                    rule_dict['citation'] = Citation(**rule_dict['citation'])
                
                rule = Rule(**rule_dict)
                
                self.rule_index[rule_id] = {
                    'embedding': rule_data['embedding'],
                    'text': rule_data['text'],
                    'rule': rule
                }
            
            print(f"Loaded {len(self.rule_index)} rules from index")
            
        except Exception as e:
            print(f"Error loading embedding index: {e}")
            import traceback
            traceback.print_exc()
    
    async def find_similar_rules(self, rule_text: str, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Find rules similar to the given rule text (for deduplication)"""
        
        if not self.rule_index:
            await self._load_index()
        
        try:
            query_embeddings = await self.lm_client.get_embeddings([rule_text])
            query_embedding = query_embeddings[0]
        except Exception as e:
            print(f"Error getting embedding for similarity check: {e}")
            return []
        
        similar_rules = []
        
        for rule_id, rule_data in self.rule_index.items():
            rule_embedding = np.array(rule_data['embedding'])
            query_emb = np.array(query_embedding)
            
            similarity = cosine_similarity(
                query_emb.reshape(1, -1), 
                rule_embedding.reshape(1, -1)
            )[0][0]
            
            if similarity >= threshold:
                similar_rules.append({
                    'rule_id': rule_id,
                    'rule': rule_data['rule'],
                    'similarity': similarity
                })
        
        similar_rules.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_rules