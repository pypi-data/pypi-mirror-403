import asyncio
from asyncio import Semaphore
from collections import defaultdict
from typing import Dict, List

from google.genai.types import File as GeminiFile

from mfcli.models.file import File
from mfcli.models.mcu_errata import ErrataIDs, ErrataItem, ErrataTopLevelSummary
from mfcli.pipeline.analysis.generators.generator_base import GeneratorBase
from mfcli.pipeline.analysis.generators.mcu_errata.instructions import (
    extract_errata_ids_instruction,
    extract_errata_instructions,
    errata_document_summary_instructions
)
from mfcli.pipeline.run_context import PipelineRunContext
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


class ErrataCheatSheetGenerator(GeneratorBase):
    def __init__(self, context: PipelineRunContext, db_file: File, uploads: List[GeminiFile]):
        super().__init__(context, db_file, uploads)

    async def _extract_errata_ids(self) -> list[str]:
        prompt = "Use the Errata file to extract errata_ids"
        errata_ids: ErrataIDs = await self._context.gemini.generate(
            prompt=prompt,
            instructions=extract_errata_ids_instruction,
            response_model=ErrataIDs,
            files=self._uploads
        )
        return errata_ids.ids

    async def _extract_errata(self, errata_id: str, sem: Semaphore) -> ErrataItem:
        prompt = f"Extract errata info from ID: {errata_id}"
        async with sem:
            return await self._context.gemini.generate(
                prompt=prompt,
                instructions=extract_errata_instructions,
                response_model=ErrataItem,
                files=self._uploads
            )

    async def _generate_top_level_summary(self) -> ErrataTopLevelSummary:
        prompt = "Generate top-level document summary"
        return await self._context.gemini.generate(
            prompt=prompt,
            instructions=errata_document_summary_instructions,
            response_model=ErrataTopLevelSummary,
            files=self._uploads
        )

    async def _create_summary(self, errata: list[ErrataItem]) -> Dict:
        critical = []
        major = []
        minor = []
        model_issues_counts = defaultdict(int)
        for erratum in errata:
            if erratum.severity == 'Critical':
                critical.append(erratum.model_dump())
            elif erratum.severity == 'Major':
                major.append(erratum.model_dump())
            else:
                minor.append(erratum.model_dump())
            for module in erratum.affected_modules:
                model_issues_counts[module] += 1
        summary = await self._generate_top_level_summary()
        return {
            "errata_cheat_sheet": {
                "mcu_name": summary.mcu_name,
                "errata_document": summary.errata_document,
                "total_issues": len(errata),
                "critical_issues": critical,
                "major_issues": major,
                "minor_issues": minor,
                "summary_by_module": model_issues_counts,
                "key_recommendations": summary.recommendations
            }
        }

    async def generate(self) -> Dict:
        errata_ids = await self._extract_errata_ids()
        errata: list[ErrataItem] = []
        sem = asyncio.Semaphore(5)
        tasks = [self._extract_errata(errata_id, sem) for errata_id in errata_ids]
        results: list[ErrataItem | Exception] = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.exception(result)
                logger.error(f"Error extracting errata")
                continue
            errata.append(result)
        return await self._create_summary(errata)
