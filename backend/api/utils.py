from .models import Event
from typing import Optional, Dict, Any

def log_event(user_id: Optional[int], action: str, movie_id: Optional[int], **ctx):
    Event.objects.create(userId=user_id, action=action, movie_id=movie_id, context=ctx)



import numpy as np
from api.models import Embedding

def bytes_to_vec(b, dim):
    return np.frombuffer(b, dtype=np.float32, count=dim)

def cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))

def more_like_this(movie_id: int, k=20):
    q = Embedding.objects.get(object_type='movie', object_id=movie_id, model_version='v1')
    qv = bytes_to_vec(q.vector, q.dim)
    cands = Embedding.objects.filter(object_type='movie', model_version='v1').exclude(object_id=movie_id)
    scored = [(e.object_id, cosine(qv, bytes_to_vec(e.vector, e.dim))) for e in cands.iterator(chunk_size=1000)]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [mid for mid, _ in scored[:k]]

