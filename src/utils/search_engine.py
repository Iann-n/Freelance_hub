"""Search engine that validates seller expertise against their services"""
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

class SearchQuery:
    def __init__(self, items):
        self.items = items
        
        # Separate the service info from resume
        self.service_texts = [
            f"TITLE: {item.title}. DESCRIPTION: {item.description}" 
            for item in items
        ]
        self.resumes = [item.resume or 'No experience listed' for item in items]
        
        # Pre-compute embeddings separately
        print("Encoding service descriptions...")
        self.service_embeddings = model.encode(self.service_texts, normalize_embeddings=True)
        
        print("Encoding resumes...")
        self.resume_embeddings = model.encode(self.resumes, normalize_embeddings=True)

    def search(self, query):
        """
        Search that considers BOTH query relevance AND expertise validation
        Returns: List of tuples [(item, score), ...] for backward compatibility
        """
        # Step 1: How well does the SERVICE match the query?
        query_embedding = model.encode(query, normalize_embeddings=True)
        service_match_scores = cosine_similarity([query_embedding], self.service_embeddings)[0]
        
        # Step 2: How well does the RESUME support the SERVICE?
        expertise_scores = []
        for i in range(len(self.items)):
            # Compare each resume to its own service description
            resume_service_similarity = cosine_similarity(
                [self.resume_embeddings[i]], 
                [self.service_embeddings[i]]
            )[0][0]
            expertise_scores.append(resume_service_similarity)
        
        expertise_scores = np.array(expertise_scores)
        
        # Step 3: Combine both scores
        final_scores = (
            0.6 * service_match_scores +      # Does service match query?
            0.4 * expertise_scores             # Does resume support service?
        )
        
        # Return tuples for backward compatibility
        ranked = sorted(
            zip(self.items, final_scores), 
            key=lambda x: x[1], 
            reverse=True
        )
        return ranked

    def search_with_explanation(self, query, top_n=5):
        """
        Same as search() but returns human-readable explanations
        """
        results = self.search(query)
        
        explained_results = []
        for r in results[:top_n]:
            item = r['item']
            explained_results.append({
                'title': item.title,
                'seller': getattr(item, 'seller_name', 'Unknown'),
                'final_score': f"{r['final_score']:.3f}",
                'service_relevance': f"{r['service_match']:.3f}",
                'expertise_validation': f"{r['expertise_score']:.3f}",
                'explanation': self._generate_explanation(r)
            })
        
        return explained_results
    
    def _generate_explanation(self, result):
        expertise = result['expertise_score']
        service = result['service_match']
        
        if expertise > 0.7 and service > 0.7:
            return "✅ Strong match - Service is relevant AND seller has proven experience"
        elif service > 0.7 and expertise < 0.5:
            return "⚠️ Service matches but seller's experience may not support it"
        elif service < 0.5:
            return "❌ Service doesn't match your search well"
        else:
            return "✓ Decent match with adequate experience"