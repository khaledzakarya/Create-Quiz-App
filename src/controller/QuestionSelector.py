from sentence_transformers import SentenceTransformer, util
from helpers.config import get_settings
import numpy as np

class QuestionSelector:
    def __init__(self, model: str = None):
        settings = get_settings()
        self.model = model or settings.EMBEDDING_MODEL
        self.embedding_model = SentenceTransformer(self.model)

    def select_diverse(self, questions, k: int):
        if k >= len(questions):
            return questions
        
        texts = [q.question for q in questions]
        embeddings = self.embedding_model.encode(texts, convert_to_tensor=True)
        sim_matrix = util.cos_sim(embeddings, embeddings).cpu().numpy()

        selected_idx = [0]
        remaining_idx = set(range(1, len(questions)))

        while len(selected_idx) < k and remaining_idx:
            best_idx, best_min_sim = None, float("inf")
            for idx in remaining_idx:
                sims = [sim_matrix[idx][sel] for sel in selected_idx]
                max_sim = max(sims)
                if max_sim < best_min_sim:
                    best_min_sim, best_idx = max_sim, idx
            selected_idx.append(best_idx)
            remaining_idx.remove(best_idx)

        return [questions[i] for i in selected_idx]