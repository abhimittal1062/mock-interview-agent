import torch
from sentence_transformers import SentenceTransformer, util
from bert_score import score as bert_score
from app.services.llm_client import call_llm

_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-mpnet-base-v2")
    return _embedding_model


async def generate_ideal_answer(question: str):
    """Use LLM to generate the ideal reference answer."""
    system = "You are an expert interviewer. Provide the ideal answer ONLY."
    prompt = f"Give the ideal answer for this interview question:\n\n{question}"

    return await call_llm(system, prompt)


def compute_semantic_similarity(user: str, ideal: str) -> float:
    """Semantic similarity via cosine between embeddings."""
    model = get_embedding_model()
    emb_user = model.encode(user, convert_to_tensor=True)
    emb_ideal = model.encode(ideal, convert_to_tensor=True)
    sim = util.cos_sim(emb_user, emb_ideal).item()
    return round(float(sim), 4)


def compute_bert_f1(user: str, ideal: str) -> float:
    """Compute BERTScore F1."""
    _, _, F1 = bert_score([user], [ideal], lang="en")
    return round(F1[0].item(), 4)
