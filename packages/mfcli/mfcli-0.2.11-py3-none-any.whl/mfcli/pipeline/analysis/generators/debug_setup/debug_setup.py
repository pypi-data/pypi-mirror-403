import asyncio
from asyncio import Semaphore
from typing import Dict, Type, List

from google.genai.types import File as GeminiFile
from pydantic import BaseModel

from mfcli.models.debug_setup import (
    DSTargetMCU,
    DebugInterface,
    DebugTool,
    DriverInfo,
    VSCodeLaunchConfig,
    DSAdditionalTools,
    DSTroubleshootingGuide,
    DSQuickStartGuide
)
from mfcli.models.file import File
from mfcli.pipeline.analysis.generators.debug_setup.instructions import (
    ds_mcu_instructions,
    ds_debug_int_instructions,
    ds_recommended_tool_instructions,
    ds_drivers_instructions,
    ds_vscode_launch_instructions,
    ds_add_tools_instructions,
    ds_troubleshooting_instructions,
    ds_quick_start_guide_instructions,
    ds_system_instructions
)
from mfcli.pipeline.analysis.generators.generator_base import GeneratorBase
from mfcli.pipeline.run_context import PipelineRunContext
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)

DSModelInstructionsMap = {
    DSTargetMCU: ds_mcu_instructions,
    DebugInterface: ds_debug_int_instructions,
    DebugTool: ds_recommended_tool_instructions,
    DriverInfo: ds_drivers_instructions,
    VSCodeLaunchConfig: ds_vscode_launch_instructions,
    DSAdditionalTools: ds_add_tools_instructions,
    DSTroubleshootingGuide: ds_troubleshooting_instructions,
    DSQuickStartGuide: ds_quick_start_guide_instructions
}


class DSCheatSheetGenerator(GeneratorBase):
    def __init__(self, context: PipelineRunContext, db_file: File, uploads: List[GeminiFile]):
        super().__init__(context, db_file, uploads)
        self._sem = Semaphore(5)

    async def _extract_ds_data(self, model: Type[BaseModel], instructions: str) -> BaseModel:
        return await self._context.gemini.generate(
            prompt=instructions,
            instructions=ds_system_instructions,
            response_model=model,
            files=self._uploads
        )

    async def generate(self) -> Dict:
        tasks = []
        for model, instructions in DSModelInstructionsMap.items():
            tasks.append(self._extract_ds_data(model, instructions))
        results: list[BaseModel] = await asyncio.gather(*tasks)
        response_dict = {}
        for result in results:
            response_dict.update(result.model_dump())
        return {
            "debug_setup": response_dict
        }
