import asyncio
from typing import Dict, Type, List

from google.genai.types import File as GeminiFile
from pydantic import BaseModel

from mfcli.models.file import File
from mfcli.models.mcu import (
    MCUData,
    MemoryMap,
    ClockConfig,
    InterruptVectors,
    StartupRequirementsModel,
    EssentialPeripherals,
    MCULinkerScriptInfo,
    MCUHelloWorldSteps,
    MCUDebuggingInterface,
    MCUProgrammingInterface,
    MCUDatasheetReferences
)
from mfcli.pipeline.analysis.generators.generator_base import GeneratorBase
from mfcli.pipeline.analysis.generators.mcu.instructions import (
    mcu_data_instruction,
    mcu_instructions_base,
    mcu_memory_map_instructions,
    mcu_clock_config_instructions,
    mcu_interrupt_vectors_instructions,
    mcu_startup_req_instructions,
    mcu_peripherals_instructions,
    mcu_linker_script_instructions,
    mcu_hello_world_instructions,
    mcu_debugging_interface_instructions,
    mcu_programming_interface_instructions,
    mcu_datasheet_references
)
from mfcli.pipeline.run_context import PipelineRunContext
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)

MCUModelInstructionsMap: Dict[Type[BaseModel], str] = {
    MCUData: mcu_data_instruction,
    MemoryMap: mcu_memory_map_instructions,
    ClockConfig: mcu_clock_config_instructions,
    InterruptVectors: mcu_interrupt_vectors_instructions,
    StartupRequirementsModel: mcu_startup_req_instructions,
    EssentialPeripherals: mcu_peripherals_instructions,
    MCULinkerScriptInfo: mcu_linker_script_instructions,
    MCUHelloWorldSteps: mcu_hello_world_instructions,
    MCUDebuggingInterface: mcu_debugging_interface_instructions,
    MCUProgrammingInterface: mcu_programming_interface_instructions,
    MCUDatasheetReferences: mcu_datasheet_references
}


class MCUCheatSheetGenerator(GeneratorBase):
    def __init__(self, context: PipelineRunContext, db_file: File, uploads: List[GeminiFile]):
        super().__init__(context, db_file, uploads)

    async def _extract_mcu_data(self, model: Type[BaseModel], instructions: str) -> BaseModel:
        return await self._context.gemini.generate(
            prompt=instructions,
            instructions=mcu_instructions_base,
            response_model=model,
            files=self._uploads
        )

    @staticmethod
    def _parse_mcu_generated_data(results: list[BaseModel]) -> Dict:
        response_json = {}
        for result in results:
            response_json.update(result.model_dump())
        return {
            "mcu_cheat_sheet": response_json
        }

    async def generate(self) -> Dict:
        logger.debug(f"Generating MCU data cheat sheet")
        tasks = []
        for model, instructions in MCUModelInstructionsMap.items():
            tasks.append(self._extract_mcu_data(model, instructions))
        results: list[BaseModel] = await asyncio.gather(*tasks)
        logger.debug(f"MCU data cheat sheet generated")
        return self._parse_mcu_generated_data(results)
