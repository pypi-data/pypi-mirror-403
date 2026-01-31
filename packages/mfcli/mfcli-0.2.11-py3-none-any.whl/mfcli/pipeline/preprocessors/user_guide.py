import asyncio
from pathlib import Path
from typing import List

from google.genai.types import File as GeminiFile
from pydantic import BaseModel, Field

from mfcli.agents.tools.general import format_instructions
from mfcli.models.file import File
from mfcli.models.pdf_parts import PDFPart
from mfcli.pipeline.run_context import PipelineRunContext
from mfcli.utils.directory_manager import app_dirs
from mfcli.utils.pdf_splitter import PDFSplitter


class TOCSection(BaseModel):
    title: str = Field(..., description="Section title")
    section_no: int = Field(..., description="Section number")
    start_page: int = Field(..., description="Starting page")
    end_page: int = Field(..., description="End page")


class TOC(BaseModel):
    sections: List[TOCSection] = Field(..., description="Table of Contents sections")


user_guide_preprocessor_instructions = format_instructions(
    """
    You will receive the start of a PDF for hardware engineering user guide. 
    Your task is to extract all the Table of Contents sections from the PDF.
    You will respond with the section title (no numbers in the title).
    You will respond separately with the section number (section_no).
    You will also respond with the start page (start_page) and (end_page) of this section. 
    You MUST respond with all relevant top-level sections in the PDF. 
    
    Here are examples of relevant top-level sections:
        
        1. Architecture
        2. PMCU
        3. CPU
        
    Here are examples of sections which are NOT relevant (content) sections (do not include these):
    
        Read This First
        About This Manual
        Glossary
        Related Documentation
        Support Resources 
        
    Here are examples of sections which are NOT top-level (do not include these):
    
        1.1 Architecture Overview
        1.2 Bus Organization
        1.3 Platform Memory Map
        
    ONLY include content sections and top-level sections. 
    """
)


class UserGuidePreprocessor:
    def __init__(
            self,
            context: PipelineRunContext,
            file: File,
            pdf_head: GeminiFile,
            content: bytes,
            splitter: PDFSplitter
    ):
        self._context = context
        self._file = file
        self._pdf_head = pdf_head
        self._content = content
        self._splitter = splitter

    async def _generate_toc(self) -> TOC:
        return await self._context.gemini.generate(
            prompt="Generate the Table of Content sections for this PDF",
            instructions=user_guide_preprocessor_instructions,
            response_model=TOC,
            files=[self._pdf_head]
        )

    async def _create_pdf_part(self, section: TOCSection, pdf_part_path: Path) -> PDFPart:
        pdf_part_gemini_file = await self._context.gemini.upload(pdf_part_path)
        self._context.gemini_file_cache[pdf_part_gemini_file.name] = pdf_part_gemini_file
        return PDFPart(
            path=str(pdf_part_path),
            file_id=self._file.id,
            gemini_file_id=pdf_part_gemini_file.name,
            start_page=section.start_page,
            end_page=section.end_page,
            title=section.title,
            section_no=section.section_no
        )

    async def preprocess(self) -> List[PDFPart]:
        toc = await self._generate_toc()
        upload_tasks = []
        for section in toc.sections:
            pdf_part_path = self._splitter.extract_range(
                start_page=section.start_page,
                end_page=section.end_page,
                output_folder=app_dirs.pdf_parts_dir
            )
            upload_tasks.append(self._create_pdf_part(section, pdf_part_path))
        pdf_parts: List[PDFPart] = await asyncio.gather(*upload_tasks)
        return pdf_parts


async def preprocess_user_guide(
        context: PipelineRunContext,
        file: File,
        pdf_head: GeminiFile,
        content: bytes,
        splitter: PDFSplitter
) -> None:
    preprocessor = UserGuidePreprocessor(
        context=context,
        file=file,
        pdf_head=pdf_head,
        content=content,
        splitter=splitter
    )
    pdf_parts = await preprocessor.preprocess()
    context.db.add_all(pdf_parts)
    context.db.commit()
