from rank_bm25 import BM25Okapi
import re

class freelance_post:
    def __init__(self,title, description, price, id, resume, seller_username, image_url = None):
        self.title = title
        self.description = description
        self.price = price
        self.id = id
        self.resume = resume
        self.seller_username = seller_username

        self.image_url = image_url or "/static/default_image.png"

    def post(self):
        return f"Post(title = {self.title}, content = {self.description})"
        

class SearchQuery:
    def __init__(self, posts):
        self.posts = posts
        self.tokenized_corpus = [
            self._tokenize(f"{post.title} {post.description}") 
            for post in posts
        ]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
    
    def _tokenize(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()
    
    def search(self, query, top_k=None):
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        results = list(zip(self.posts, scores))
        results.sort(key=lambda x: x[1], reverse=True)
        
        if top_k:
            results = results[:top_k]
        return results