import asyncio
from asyncio import Semaphore
from typing import Dict, Type, List

from google.genai.types import File
from pydantic import BaseModel, Field

from mfcli.client.gemini import Gemini
from mfcli.models.bom import BOMSchema
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)

system_instructions = (
    """
    You are the BOM Generator agent. Your role is to extract components from PDF schematics
    and generate a Bill of Materials (BOM) in CSV format.
    """
)

identify_bom_entries_instructions = (
    """
    You will return a list of names for Bill of Materials (BOM) entries from this schematic file.
    """
)

generate_bom_entry_instructions = (
    """
    Analyze the schematic and extract BOM entry data for component: {}:
    - Reference designators (R1, C1, U1, etc.)
    - Component values (10kΩ, 100nF, etc.)
    - Part numbers and manufacturers (if visible)
    - Footprints/packages (if visible)
    - Any other available information
    """
)


class BOMEntryNames(BaseModel):
    names: List[str] = Field(default_factory=list, description="BOM entry names")


class BOMGenerator:
    def __init__(self, gemini: Gemini):
        self._gemini = gemini
        self._sem = Semaphore(5)

    async def _generate(self, file: File, model: Type[BaseModel], instructions: str) -> BaseModel:
        async with self._sem:
            return await self._gemini.generate(
                prompt=instructions,
                instructions=system_instructions,
                response_model=model,
                files=[file]
            )

    async def _get_bom_entry_names(self, file: File) -> List[str]:
        response = await self._generate(file, BOMEntryNames, identify_bom_entries_instructions)
        return response.names

    async def generate(self, file: File) -> List[Dict]:
        bom_entry_names = await self._get_bom_entry_names(file)
        tasks = []
        for name in bom_entry_names:
            bom_entry_instructions = generate_bom_entry_instructions.format(name)
            tasks.append(self._generate(file, BOMSchema, bom_entry_instructions))
        results: List[BOMSchema | Exception] = await asyncio.gather(*tasks, return_exceptions=True)
        response_data = []
        for result in results:
            if isinstance(result, Exception):
                logger.warn(f"There was an error generating BOM entry data: {result}")
                continue
            response_data.append(result.model_dump())
        return response_data
