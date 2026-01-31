from typing import List, Dict

from google.genai.types import File as GeminiFile

from mfcli.models.file import File
from mfcli.models.llm_response import LLMResponse
from mfcli.models.pdf_parts import PDFPart
from mfcli.pipeline.analysis.generators.generator_base import GeneratorBase
from mfcli.pipeline.run_context import PipelineRunContext

user_guide_summary_instructions = (
    """
    You will receive sections of a hardware engineering user guide PDF. 
    Your job is to summarize those sections. 
    You will also receive the sections that have been summarized so far. 
    Use the sections that have been summarized as context to generate new summaries. 
    ONLY output the summary text, no other information.
    The summary text will be read directly by users. 
    """
)


class SummaryCheatSheetGenerator(GeneratorBase):
    def __init__(self, context: PipelineRunContext, db_file: File, uploads: List[GeminiFile]):
        super().__init__(context, db_file, uploads)

    async def generate(self) -> Dict:
        pdf_parts: List[PDFPart] = self._file.pdf_parts
        pdf_parts.sort(key=lambda part: part.section_no)
        summaries = []
        for pdf_part in pdf_parts:
            prompt = f"Summarize the {pdf_part.title} section\n\nCurrent summaries:\n\n{summaries}"
            upload = self._context.gemini_file_cache[pdf_part.gemini_file_id]
            response: LLMResponse = await self._context.gemini.generate(
                prompt=prompt,
                instructions=user_guide_summary_instructions,
                response_model=LLMResponse,
                files=[upload]
            )
            summaries.append({
                "no": pdf_part.section_no,
                "title": pdf_part.title,
                "summary": response.text
            })
        return {
            "summaries": summaries
        }
