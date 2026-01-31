from typing import Dict

from google.genai.types import File as GeminiFile
from mfcli.utils.query_service import QueryService

from mfcli.client.gemini import Gemini
from mfcli.models.file_docket import FileDocket
from mfcli.models.pipeline_run import PipelineRun
from mfcli.models.project_metadata import ProjectConfig
from mfcli.utils.datasheet_vectorizer import DatasheetVectorizer
from mfcli.utils.orm import Session


class PipelineRunContext:
    def __init__(
            self,
            db: Session,
            pipeline_run: PipelineRun,
            gemini: Gemini,
            gemini_file_cache: Dict[str, GeminiFile],
            docket: FileDocket,
            config: ProjectConfig,
            vectorizer: DatasheetVectorizer
    ):
        self.db = db
        self.run = pipeline_run
        self.gemini = gemini
        self.gemini_file_cache = gemini_file_cache
        self.docket = docket
        self.config = config
        self.vectorizer = vectorizer
        self.query_service = QueryService(self.db)
