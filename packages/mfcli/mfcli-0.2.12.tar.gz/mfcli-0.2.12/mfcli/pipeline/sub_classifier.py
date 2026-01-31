from typing import Literal

from google.genai.types import File as GeminiFile
from pydantic import BaseModel

from mfcli.agents.tools.general import format_instructions
from mfcli.client.gemini import Gemini
from mfcli.constants.file_types import (
    FileTypes,
    FileSubtypes,
    FILE_SUBTYPE_UNKNOWN,
    PDFSubtypeDescriptions,
    OtherFileTypeDescriptions,
    PDFFileSubtypeNames,
    OtherFileSubtypeNames
)
from mfcli.models.file import File
from mfcli.pipeline.parsers.netlist.kicad_legacy_net import is_kicad_legacy_netlist
from mfcli.pipeline.parsers.netlist.protel_detector import is_protel_netlist
from mfcli.pipeline.parsers.schematic.kicad_sch_detector import is_kicad_schematic
from mfcli.utils.files import is_text_mime_type
from mfcli.utils.logger import get_logger

sub_classifier_instructions = format_instructions(
    """
    You are the sub-classifier agent for an engineering document processing pipeline. 
    You will receive the first 50 lines of text from a file.
    You will examine the content of the file, and determine the sub-type of this file. 
    You will be given the sub-types and sub-type descriptions. 
    If you are not able to determine the sub-type you will respond with "UNKNOWN". 
    
    Here are the valid sub-types and a description of each:

    {}
    
    """
)

logger = get_logger(__name__)


class PDFSubtypeClassifierResponse(BaseModel):
    type: PDFFileSubtypeNames


class OtherFileSubtypeClassifierResponse(BaseModel):
    type: OtherFileSubtypeNames


FileClass = Literal['pdf', 'other']


class FileSubtypeAnalyzer:
    def __init__(self, gemini: Gemini):
        self._gemini = gemini

    async def _get_subtype_from_gemini(
            self,
            prompt: str,
            instructions: str,
            gemini_file: GeminiFile | None = None,
            file_class: FileClass = 'other'
    ) -> str:
        model = OtherFileSubtypeClassifierResponse if file_class == 'other' else PDFSubtypeClassifierResponse
        files = [gemini_file] if gemini_file else None
        response = await self._gemini.generate(
            prompt=prompt,
            instructions=instructions,
            response_model=model,
            files=files
        )
        return response.type

    async def _get_subtype(
            self,
            prompt: str,
            file: File,
            gemini_file: GeminiFile | None = None,
            file_class: FileClass = 'other'
    ) -> None:
        logger.debug(f"Fetching subtype for file: {file.name}")
        relevant_subtype_descriptions = PDFSubtypeDescriptions if file.type == FileTypes.PDF else OtherFileTypeDescriptions
        logger.debug(f"Relevant subtypes: {relevant_subtype_descriptions.keys()}")
        instructions = sub_classifier_instructions.format(relevant_subtype_descriptions)
        subtype = await self._get_subtype_from_gemini(prompt, instructions, gemini_file, file_class)
        logger.debug(f"Subtype discovered: {subtype}")
        if subtype == FILE_SUBTYPE_UNKNOWN:
            logger.warning(f"Could not determine the file subtype for file: {file.name}, using UNKNOWN")
            file.sub_type = FileSubtypes.UNKNOWN.value
            return
        if not subtype in relevant_subtype_descriptions:
            raise RuntimeError(f"LLM responded with invalid subtype: {subtype}")
        file.sub_type = FileSubtypes.get(subtype)

    async def analyze_pdf(
            self,
            file: File,
            gemini_file: GeminiFile
    ) -> None:
        prompt = "Determine this PDF file subtype"
        await self._get_subtype(prompt, file, gemini_file, 'pdf')

    async def analyze_file(
            self,
            file: File,
            text: str
    ) -> None:
        # Handle file types based on extension first
        # KiCad schematic files (.kicad_sch) are always SCHEMATIC subtype
        if file.type == FileTypes.KICAD_SCH:
            file.sub_type = FileSubtypes.SCHEMATIC.value
            return
        
        # Generic document file types (TXT, RTF, DOCX, JPG) default to UNKNOWN
        # These files will be vectorized but not analyzed for specific subtypes
        if file.type in (FileTypes.TXT, FileTypes.RTF, FileTypes.DOCX, FileTypes.JPG):
            file.sub_type = FileSubtypes.UNKNOWN.value
            logger.info(f"File type {FileTypes(file.type).name} auto-assigned UNKNOWN subtype")
            return
        
        # Handle text MIME types for content-based detection
        if text and is_text_mime_type(file.mime_type):
            if file.type == FileTypes.NET:
                if is_kicad_legacy_netlist(text):
                    file.sub_type = FileSubtypes.KICAD_LEGACY_NET.value
                elif is_protel_netlist(text):
                    file.sub_type = FileSubtypes.PROTEL_ALTIUM.value

        # If subtype cannot be parsed, use LLM to determine subtype
        if not file.sub_type:
            await self._get_subtype(text[0:500], file)
