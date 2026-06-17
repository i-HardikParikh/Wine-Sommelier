import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from loguru import logger

from app.models.db_models import EvalRun
from app.models.enums import EvalMetric
from app.models.schemas import EvalResult, EvalScore, EvalSample
from app.services.agentic_rag_service import run_query
from app.utils.llm_client import get_llm_client

_llm = get_llm_client()

# ─── Built-in eval questions ─────────────────────────────────────────────────

DEFAULT_EVAL_SAMPLES = [
    EvalSample(question="What wine pairs best with a rich ribeye steak?"),
    EvalSample(question="Recommend a white wine for a light summer salad."),
    EvalSample(question="What is the difference between Burgundy and Bordeaux?"),
    EvalSample(question="Which regions produce the best Pinot Noir?"),
    EvalSample(question="How should I store opened wine?"),
    EvalSample(question="What is terroir?"),
    EvalSample(question="Recommend an affordable Champagne for a celebration."),
    EvalSample(question="What wine goes well with spicy Thai food?"),
    EvalSample(question="Explain the difference between old world and new world wines."),
    EvalSample(question="What is the ideal serving temperature for a Cabernet Sauvignon?"),
]

JUDGE_SYSTEM = """You are an expert wine sommelier and AI evaluator. 
Score the assistant's wine answer on the given metric from 0.0 to 1.0.
Return ONLY valid JSON: {"score": <float>, "reasoning": "<one sentence>"}"""

METRIC_PROMPTS = {
    EvalMetric.RELEVANCE: "Does the answer directly address the wine question asked? Score 1.0 if perfectly on-topic, 0.0 if completely off-topic.",
    EvalMetric.FAITHFULNESS: "Is the answer factually accurate about wine? Score 1.0 if all facts are correct, 0.0 if there are clear errors.",
    EvalMetric.COMPLETENESS: "Does the answer cover all aspects of the question comprehensively? Score 1.0 if thorough, 0.0 if missing key points.",
    EvalMetric.SOMMELIER_TONE: "Does the answer sound like an expert, warm, elegant sommelier? Score 1.0 if professional and engaging, 0.0 if robotic or generic.",
}


def _judge_answer(question: str, answer: str, metric: EvalMetric) -> EvalScore:
    """Use the configured judge LLM (OpenAI primary, Groq fallback) to score one metric."""
    prompt = f"{METRIC_PROMPTS[metric]}\n\nQuestion: {question}\nAnswer: {answer}"
    try:
        raw = _llm.chat_json(
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            kind="eval",
        )
        data = json.loads(raw)
        return EvalScore(
            metric=metric,
            score=float(data.get("score", 0.5)),
            reasoning=data.get("reasoning", ""),
        )
    except Exception as e:
        logger.warning(f"Judge failed for {metric}: {e}")
        return EvalScore(metric=metric, score=0.5, reasoning="Evaluation failed.")


def evaluate_sample(sample: EvalSample) -> EvalResult:
    """Run the RAG pipeline on a sample and score it on all metrics."""
    result = run_query(sample.question)
    answer = result["answer"]

    scores = [_judge_answer(sample.question, answer, m) for m in EvalMetric]
    overall = round(sum(s.score for s in scores) / len(scores), 3)

    return EvalResult(
        sample_id=str(uuid.uuid4()),
        question=sample.question,
        answer=answer,
        scores=scores,
        overall_score=overall,
        evaluated_at=datetime.utcnow(),
    )


def run_eval_suite(
    db: Session,
    user_id: int,
    num_samples: int = 10,
    custom_samples: Optional[List[EvalSample]] = None,
) -> str:
    """
    Launch a full evaluation run.
    Saves results to DB and returns run_id.
    """
    run_id = str(uuid.uuid4())
    samples = (custom_samples or DEFAULT_EVAL_SAMPLES)[:num_samples]

    eval_run = EvalRun(
        run_id=run_id,
        user_id=user_id,
        status="running",
        num_samples=len(samples),
        started_at=datetime.utcnow(),
    )
    db.add(eval_run)
    db.commit()

    results = []
    for i, sample in enumerate(samples):
        logger.info(f"Evaluating sample {i+1}/{len(samples)}: {sample.question[:50]}...")
        result = evaluate_sample(sample)
        results.append(result)

    # Aggregate per-metric averages
    aggregate: Dict[str, float] = {}
    for metric in EvalMetric:
        metric_scores = [
            s.score
            for r in results
            for s in r.scores
            if s.metric == metric
        ]
        aggregate[metric.value] = round(sum(metric_scores) / len(metric_scores), 3) if metric_scores else 0.0

    # Persist
    eval_run.status = "completed"
    eval_run.results_json = json.dumps([r.model_dump(mode="json") for r in results])
    eval_run.aggregate_json = json.dumps(aggregate)
    eval_run.completed_at = datetime.utcnow()
    db.commit()

    logger.info(f"Eval run {run_id} complete. Overall avg: {sum(aggregate.values())/len(aggregate):.3f}")
    return run_id


def get_eval_results(db: Session, run_id: str, user_id: int) -> Optional[dict]:
    """Retrieve a completed eval run's results."""
    run = db.query(EvalRun).filter(
        EvalRun.run_id == run_id,
        EvalRun.user_id == user_id,
    ).first()
    if not run:
        return None

    return {
        "run_id": run.run_id,
        "status": run.status,
        "num_samples": run.num_samples,
        "results": json.loads(run.results_json or "[]"),
        "aggregate_scores": json.loads(run.aggregate_json or "{}"),
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }
