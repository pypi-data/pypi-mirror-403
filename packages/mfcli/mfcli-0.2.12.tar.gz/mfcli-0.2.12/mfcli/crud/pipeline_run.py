from typing import Optional
from mfcli.models.pipeline_run import PipelineRun
from mfcli.models.project import Project
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)


def create_pipeline_run(db: Session, project: Project) -> PipelineRun:
    logger.debug("Creating pipeline run")
    run = PipelineRun()
    run.project = project
    db.add(run)
    db.flush()
    logger.debug(f"Pipeline run created: {run.id}")
    db.commit()
    return run


def get_latest_pipeline_run(db: Session, project_id: int) -> Optional[PipelineRun]:
    """
    Get the most recent pipeline run for a project.
    
    Args:
        db: Database session
        project_id: Project ID
    
    Returns:
        Latest PipelineRun or None if no runs exist
    """
    logger.debug(f"Getting latest pipeline run for project: {project_id}")
    run = (
        db.query(PipelineRun)
        .filter(PipelineRun.project_id == project_id)
        .order_by(PipelineRun.created_at.desc())
        .first()
    )
    return run
