from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.middleware.auth_dep import get_authenticated_user
from app.models.database import get_db
from app.models.db_models import User
from app.models.schemas import EvalRunRequest, EvalRunResponse
from app.services.eval_service import run_eval_suite, get_eval_results

router = APIRouter(prefix="/eval", tags=["LLM-as-Judge Evaluation"])


@router.post("/run", summary="Run the LLM-as-judge evaluation suite")
def start_eval(
    req: EvalRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    """
    Runs the full eval suite synchronously. For large num_samples,
    consider wrapping in a BackgroundTask or Celery worker.
    """
    run_id = run_eval_suite(
        db=db,
        user_id=current_user.id,
        num_samples=req.num_samples,
        custom_samples=req.custom_samples,
    )
    return {"run_id": run_id, "status": "completed", "message": f"Evaluation complete. Use GET /eval/results/{run_id} for results."}


@router.get("/results/{run_id}", summary="Get evaluation run results")
def fetch_results(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    result = get_eval_results(db, run_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Eval run not found.")
    return result


@router.get("/results", summary="List all evaluation runs for current user")
def list_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_authenticated_user),
):
    from app.models.db_models import EvalRun
    import json
    runs = db.query(EvalRun).filter(EvalRun.user_id == current_user.id).order_by(EvalRun.started_at.desc()).all()
    return [
        {
            "run_id": r.run_id,
            "status": r.status,
            "num_samples": r.num_samples,
            "aggregate_scores": json.loads(r.aggregate_json or "{}"),
            "started_at": r.started_at,
            "completed_at": r.completed_at,
        }
        for r in runs
    ]
