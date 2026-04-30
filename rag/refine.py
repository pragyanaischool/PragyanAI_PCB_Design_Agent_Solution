# rag/refine.py

from typing import List, Dict, Any
import os

# Optional LLM (Groq)
try:
    from groq import Groq
    GROQ_ENABLED = True
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception:
    GROQ_ENABLED = False
    client = None


# ==================================================
# BASIC CONTEXT MERGE (SAFE FALLBACK)
# ==================================================
def simple_refine(answer: str, docs: List[Dict[str, Any]]) -> str:
    """
    Append relevant context to answer
    """

    if not docs:
        return answer

    context = "\n".join([d["text"] for d in docs[:5]])

    return f"""
{answer}

--- Supporting Context ---
{context}
"""


# ==================================================
# LLM-BASED REFINEMENT
# ==================================================
def llm_refine(answer: str, docs: List[Dict[str, Any]]) -> str:
    """
    Improve answer using LLM
    """

    if not GROQ_ENABLED or not client:
        return simple_refine(answer, docs)

    context = "\n".join([d["text"] for d in docs])

    prompt = f"""
You are improving a PCB design answer.

Original Answer:
{answer}

Context:
{context}

Refine the answer:
- Make it clearer
- Add missing technical detail
- Remove redundancy
"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception:
        return simple_refine(answer, docs)


# ==================================================
# CONFIDENCE SCORING
# ==================================================
def compute_confidence(answer: str, docs: List[Dict[str, Any]]) -> float:
    """
    Basic heuristic confidence score
    """

    if not docs:
        return 0.3

    score = min(len(docs) * 0.15, 1.0)

    if len(answer) > 200:
        score += 0.1

    return min(score, 1.0)


# ==================================================
# MAIN REFINEMENT FUNCTION
# ==================================================
def refine_answer(
    answer: str,
    docs: List[Dict[str, Any]],
    use_llm: bool = True
) -> str:
    """
    Main refinement pipeline
    """

    if not answer:
        return "⚠️ No answer generated"

    if use_llm:
        refined = llm_refine(answer, docs)
    else:
        refined = simple_refine(answer, docs)

    confidence = compute_confidence(refined, docs)

    return f"""
{refined}

--- Confidence Score ---
{round(confidence, 2)}
"""


# ==================================================
# MULTI-PASS REFINEMENT (ADVANCED)
# ==================================================
def multi_pass_refine(
    answer: str,
    docs: List[Dict[str, Any]],
    passes: int = 2
) -> str:
    """
    Iteratively refine answer
    """

    refined = answer

    for _ in range(passes):
        refined = refine_answer(refined, docs)

    return refined


# ==================================================
# DEBUG
# ==================================================
if __name__ == "__main__":
    sample_answer = "R1 is a resistor"
    sample_docs = [
        {"text": "Resistors limit current"},
        {"text": "They control voltage"}
    ]

    print(refine_answer(sample_answer, sample_docs))
  
