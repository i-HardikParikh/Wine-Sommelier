"""
Manual QA script for the Wine Sommelier RAG pipeline.

Run this against your LIVE backend (uvicorn must be running) before submitting
the project. It fires a curated set of questions designed to exercise every
branch of the LangGraph pipeline, prints the answer + which nodes fired, and
flags obviously broken responses.

Usage:
    1. Start the backend:  uvicorn app.main:app --reload
    2. (Optional) Ingest a wine PDF/PPTX via /ingest/document so the
       "text_chunks_found" and "vision"/"ocr" cases have something to retrieve.
    3. Run:  python scripts/manual_qa.py
    4. Read the PASS/WARN/FAIL summary at the bottom.

This does NOT replace the automated pytest suite (tests/) — it's for sanity-
checking real model output quality, which automated tests can't judge well.
"""
import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000"

# ─── Step 0: register/login a throwaway QA user ──────────────────────────────

QA_EMAIL = "qa_reviewer@sommelier.local"
QA_PASSWORD = "qa_password_123"


def get_token() -> str:
    # Try login first; register if the user doesn't exist yet.
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": QA_EMAIL, "password": QA_PASSWORD})
    if resp.status_code == 200:
        return resp.json()["access_token"]

    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "email": QA_EMAIL, "password": QA_PASSWORD, "full_name": "QA Reviewer",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


# ─── Test query set ───────────────────────────────────────────────────────────
# Each entry documents WHY it's included and what "good" looks like.

QUERIES = [
    # ── Category 1: Pure LLM fallback (no documents ingested) ──────────────
    # These should hit analyze_query -> vector_search -> (no chunks) ->
    # answer_synthesis -> fallback, since there's nothing in Pinecone yet
    # unless you've ingested documents.
    {
        "category": "Fallback (general wine knowledge)",
        "question": "What wine pairs best with a rich ribeye steak?",
        "expect_contains_any": ["cabernet", "syrah", "malbec", "tannin", "red wine"],
        "expect_pipeline_includes": ["analyze_query", "vector_search"],
        "notes": "Should give a confident, specific recommendation even with an empty knowledge base.",
    },
    {
        "category": "Fallback (general wine knowledge)",
        "question": "What is the difference between Burgundy and Bordeaux wines?",
        "expect_contains_any": ["pinot noir", "cabernet", "merlot", "blend", "single varietal", "region"],
        "expect_pipeline_includes": ["analyze_query"],
        "notes": "Tests factual recall — should correctly distinguish single-varietal Burgundy vs Bordeaux blends.",
    },
    {
        "category": "Fallback (general wine knowledge)",
        "question": "What is terroir?",
        "expect_contains_any": ["soil", "climate", "environment", "region", "terrain"],
        "expect_pipeline_includes": ["analyze_query"],
        "notes": "Definitional question — answer should explain the concept clearly, not just repeat the word.",
    },

    # ── Category 2: Document-grounded (requires ingestion first) ───────────
    # Upload a wine list / catalog PDF before running these, otherwise they'll
    # also fall back to general knowledge (which is fine, but won't test
    # retrieval).
    {
        "category": "Document-grounded retrieval",
        "question": "What wines are in your current catalog?",
        "expect_contains_any": [],  # depends entirely on your uploaded doc
        "expect_pipeline_includes": ["vector_search", "answer_synthesis"],
        "notes": "If you've ingested a document, sources[] in the response should be non-empty and "
                 "name your actual uploaded filename. If sources[] is empty here, retrieval may not be working.",
    },
    {
        "category": "Document-grounded retrieval",
        "question": "What does the chart/table in the document say about ratings or scores?",
        "expect_contains_any": [],
        "expect_pipeline_includes": ["vision_analysis"],
        "notes": "Only meaningful if your ingested document contains an image with a chart/table. "
                 "Checks the vision_analysis branch actually fires and extracts structured data.",
    },

    # ── Category 3: Conversation memory ─────────────────────────────────────
    # These two MUST be sent in the same session (the script reuses session_id
    # automatically) to test that follow-up context carries over correctly.
    {
        "category": "Conversation memory (turn 1)",
        "question": "Recommend a red wine for a dinner party.",
        "expect_contains_any": ["cabernet", "merlot", "pinot", "syrah", "red wine", "malbec"],
        "expect_pipeline_includes": ["analyze_query"],
        "notes": "Sets up context for the follow-up question below.",
        "memory_key": "dinner_party_thread",
    },
    {
        "category": "Conversation memory (turn 2 — follow-up)",
        "question": "What food would go well with that?",
        "expect_contains_any": ["pair", "food", "dish", "serve", "meat", "cheese"],
        "expect_pipeline_includes": ["analyze_query"],
        "notes": "CRITICAL TEST: the answer must reference the wine recommended in turn 1 — "
                 "if it asks 'which wine do you mean?' or gives a generic answer with no connection "
                 "to the previous message, conversation memory is broken.",
        "memory_key": "dinner_party_thread",
    },

    # ── Category 4: Edge cases / robustness ─────────────────────────────────
    {
        "category": "Edge case — off-topic query",
        "question": "What's the weather like in Paris today?",
        "expect_contains_any": [],
        "expect_pipeline_includes": ["analyze_query"],
        "notes": "Should be classified as 'general' and the sommelier should gracefully redirect "
                 "or note this is outside wine expertise — NOT hallucinate a weather report.",
        "is_negative_test": True,
    },
    {
        "category": "Edge case — very short query",
        "question": "Wine?",
        "expect_contains_any": [],
        "expect_pipeline_includes": ["analyze_query"],
        "notes": "Should not crash; should ask a clarifying question or give a general wine intro.",
    },
    {
        "category": "Edge case — multi-part question",
        "question": "I'm having grilled salmon and want a light white wine under $25 — what do you suggest, and why does that pairing work?",
        "expect_contains_any": ["sauvignon blanc", "pinot grigio", "chardonnay", "albariño", "white wine"],
        "expect_pipeline_includes": ["analyze_query", "answer_synthesis"],
        "notes": "Tests whether the model addresses BOTH the recommendation AND the reasoning, not just one half.",
    },
    {
        "category": "Edge case — ambiguous/vague",
        "question": "Is this wine good?",
        "expect_contains_any": [],
        "expect_pipeline_includes": ["analyze_query"],
        "notes": "No specific wine was named. Good behavior = ask which wine, or explain it needs more "
                 "detail. Bad behavior = confidently reviewing a made-up wine.",
        "is_negative_test": True,
    },
]


def run_qa():
    print(f"\n{'='*70}\nWine Sommelier — Manual QA Run\n{'='*70}\n")

    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    session_ids = {}  # memory_key -> session_id, so follow-ups stay in the same thread
    results = []

    for i, q in enumerate(QUERIES, 1):
        session_id = session_ids.get(q.get("memory_key"))

        print(f"\n[{i}/{len(QUERIES)}] {q['category']}")
        print(f"  Q: {q['question']}")

        t0 = time.time()
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/query",
                json={"question": q["question"], "session_id": session_id},
                headers=headers,
                timeout=60,
            )
            elapsed = (time.time() - t0) * 1000
        except requests.RequestException as e:
            print(f"  ❌ FAIL — request error: {e}")
            results.append({"query": q["question"], "status": "FAIL", "reason": str(e)})
            continue

        if resp.status_code != 200:
            print(f"  ❌ FAIL — HTTP {resp.status_code}: {resp.text[:200]}")
            results.append({"query": q["question"], "status": "FAIL", "reason": f"HTTP {resp.status_code}"})
            continue

        data = resp.json()
        answer = data.get("answer", "")
        pipeline = data.get("pipeline_path", [])
        sources = data.get("sources", [])

        if q.get("memory_key"):
            session_ids[q["memory_key"]] = data.get("session_id")

        print(f"  A: {answer[:300]}{'...' if len(answer) > 300 else ''}")
        print(f"  Pipeline: {' → '.join(pipeline)}")
        print(f"  Sources: {sources or '(none)'}")
        print(f"  Latency: {elapsed:.0f}ms")

        # ─── Automated sanity checks ────────────────────────────────────────
        status = "PASS"
        reasons = []

        if not answer.strip():
            status = "FAIL"
            reasons.append("Empty answer.")

        if len(answer.strip()) < 20 and not q.get("is_negative_test"):
            status = "WARN"
            reasons.append("Suspiciously short answer.")

        expected_keywords = q.get("expect_contains_any", [])
        if expected_keywords:
            found = any(kw.lower() in answer.lower() for kw in expected_keywords)
            if not found:
                status = "WARN" if status == "PASS" else status
                reasons.append(f"None of expected keywords found: {expected_keywords}")

        expected_nodes = q.get("expect_pipeline_includes", [])
        missing_nodes = [n for n in expected_nodes if n not in pipeline]
        if missing_nodes:
            status = "WARN" if status == "PASS" else status
            reasons.append(f"Expected pipeline nodes not triggered: {missing_nodes}")

        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[status]
        print(f"  {icon} {status}" + (f" — {'; '.join(reasons)}" if reasons else ""))
        if q.get("notes"):
            print(f"  ℹ️  {q['notes']}")

        results.append({"query": q["question"], "status": status, "reason": "; ".join(reasons)})

    # ─── Summary ────────────────────────────────────────────────────────────
    print(f"\n{'='*70}\nSUMMARY\n{'='*70}")
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"  ✅ PASS: {passed}   ⚠️  WARN: {warned}   ❌ FAIL: {failed}   (of {len(results)} total)\n")

    if failed:
        print("  Failures (must fix before submitting):")
        for r in results:
            if r["status"] == "FAIL":
                print(f"    - {r['query']}: {r['reason']}")

    if warned:
        print("\n  Warnings (review manually — may be expected if no docs ingested):")
        for r in results:
            if r["status"] == "WARN":
                print(f"    - {r['query']}: {r['reason']}")

    print()
    return failed == 0


if __name__ == "__main__":
    ok = run_qa()
    sys.exit(0 if ok else 1)
