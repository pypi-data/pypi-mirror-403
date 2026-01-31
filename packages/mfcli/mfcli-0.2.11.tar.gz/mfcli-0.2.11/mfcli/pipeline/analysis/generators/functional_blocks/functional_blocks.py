import asyncio
from asyncio import Semaphore
from typing import Type, List, Dict

from google.genai.types import File
from pydantic import BaseModel

from mfcli.client.gemini import Gemini
from mfcli.crud.functional_blocks import create_functional_blocks
from mfcli.models.functional_blocks import FunctionalBlocks, FunctionalBlockMeta
from mfcli.models.pipeline_run import PipelineRun
from mfcli.pipeline.analysis.generators.functional_blocks.instructions import (
    fb_extractor_system_instructions,
    fb_extractor_identify_instructions,
    fb_extractor_fb_meta_instructions
)
from mfcli.pipeline.analysis.generators.functional_blocks.validator import validate_functional_blocks_against_netlist
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)

FBExtractedData = FunctionalBlocks | FunctionalBlockMeta


class FBCheatSheetGenerator:
    def __init__(self, gemini: Gemini, files: List[File]):
        self._gemini = gemini
        self._sem = Semaphore(5)
        self._files = files

    async def _extract_fb_data(self, model: Type[BaseModel], instructions: str) -> FBExtractedData:
        return await self._gemini.generate(
            prompt=instructions,
            instructions=fb_extractor_system_instructions,
            response_model=model,
            files=self._files
        )

    async def _retrieve_fb_list(self) -> list[str]:
        blocks = await self._extract_fb_data(FunctionalBlocks, fb_extractor_identify_instructions)
        return blocks.functional_blocks

    async def _generate_fb_data(self, name: str) -> FunctionalBlockMeta:
        block_instructions = fb_extractor_fb_meta_instructions.format(name)
        return await self._extract_fb_data(FunctionalBlockMeta, block_instructions)

    async def _generate_single_block(self, name: str) -> FunctionalBlockMeta:
        async with self._sem:
            return await self._generate_fb_data(name)

    async def generate(self) -> List[FunctionalBlockMeta]:
        blocks = await self._retrieve_fb_list()
        tasks = []
        for block in blocks:
            tasks.append(self._generate_single_block(block))
        responses = await asyncio.gather(*tasks)
        block_data = []
        for response in responses:
            if isinstance(response, Exception):
                continue
            block_data.append(response)
        return block_data


def _get_functional_blocks_dict(blocks: List[FunctionalBlockMeta]) -> Dict:
    return {
        "functional_blocks": [block.model_dump() for block in blocks]
    }


async def extract_functional_blocks_from_file(
        db: Session,
        pipeline_run: PipelineRun,
        gemini: Gemini,
        schematic_files: List[File] | None = None,
        user_guide_files: List[File] | None = None,
        netlist_file: File | None = None
) -> Dict:
    if not schematic_files and not user_guide_files and not netlist_file:
        error = "At least one of these file types must be specified: [schematic, user_guide, netlist]"
        raise ValueError(error)
    files = []
    if schematic_files:
        files += schematic_files
    if user_guide_files:
        files += user_guide_files
    if netlist_file:
        files.append(netlist_file)
    blocks = await FBCheatSheetGenerator(gemini, files).generate()
    validate_functional_blocks_against_netlist(db, pipeline_run.id, blocks)
    create_functional_blocks(db, pipeline_run, blocks)
    return _get_functional_blocks_dict(blocks)
