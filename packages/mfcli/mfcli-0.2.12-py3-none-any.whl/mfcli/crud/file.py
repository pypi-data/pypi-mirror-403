from mfcli.models.file import File
from mfcli.models.file_metadata import FileMetadata
from mfcli.models.pipeline_run import PipelineRun
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)


def create_file(db: Session, pipeline_run_id: int, metadata: FileMetadata) -> File:
    logger.debug(f"Creating file: {metadata.name}")
    existing_file: File | None = (
        db.query(File)
        .filter(File.md5 == metadata.md5)
        .filter(File.pipeline_run_id == pipeline_run_id)
        .one_or_none()
    )
    if existing_file:
        raise ValueError(f"File {metadata.name} already exists and will not be processed")

    pipeline_run: PipelineRun = (
        db.query(PipelineRun)
        .filter(PipelineRun.id == pipeline_run_id)
        .one_or_none()
    )
    if not pipeline_run:
        raise ValueError(f"Pipeline run ID does not exist: {pipeline_run_id}")

    file = File(
        name=metadata.name,
        type=metadata.type_id,
        mime_type=metadata.mime,
        md5=metadata.md5,
        path=str(metadata.path),
        ext=metadata.ext,
        is_datasheet=int(metadata.is_datasheet)
    )
    file.pipeline_run = pipeline_run
    db.add(file)
    db.flush()
    logger.debug(f"File created: {file.id}")
    return file
