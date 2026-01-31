from abc import abstractmethod
from typing import List, Dict

from google.genai.types import File as GeminiFile

from mfcli.models.file import File
from mfcli.pipeline.run_context import PipelineRunContext


class GeneratorBase:
    def __init__(self, context: PipelineRunContext, db_file: File, uploads: List[GeminiFile]):
        self._context = context
        self._file = db_file
        self._uploads: List[GeminiFile] = uploads

    @abstractmethod
    async def generate(self) -> Dict:
        pass
