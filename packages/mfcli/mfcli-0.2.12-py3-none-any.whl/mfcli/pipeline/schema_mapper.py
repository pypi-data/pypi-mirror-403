from typing import Type, Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel

from mfcli.agents.tools.general import format_instructions
from mfcli.client.gemini import Gemini
from mfcli.constants.file_types import FileSubtypes
from mfcli.models.bom import BOM, BOMSchema
from mfcli.models.netlist import Netlist
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)

SubtypeSchemas: dict[FileSubtypes, Type[BaseModel]] = {
    FileSubtypes.BOM: BOMSchema
}
SubtypeModels: dict[FileSubtypes, Type[SQLModel]] = {
    FileSubtypes.BOM: BOM,
    FileSubtypes.KICAD_LEGACY_NET: Netlist,
    FileSubtypes.PADS_PCB_ASCII: Netlist,
    FileSubtypes.KICAD_SPICE: Netlist,
    FileSubtypes.PROTEL_ALTIUM: Netlist
}


class SchemaMapping(BaseModel):
    input_field: Optional[str] = Field(None, description="A field found in the sample file")
    mapped_field: str = Field(..., description="The field found in the backend to be mapped to")


class SchemaMappings(BaseModel):
    fields: list[SchemaMapping] = Field(default_factory=list, description="List of schema mappings")


schema_mapper_instructions = format_instructions(
    """
    You are responsible for mapping fields found in a file to a backend schema.
    You will be given the schema for a file subtype, like Bill of Materials (BOM). 
    You will map whatever fields you see in the file, to fields in the backend. 
    For example, a column "Designator" found in a BOM file would map to "reference" in the backend.
    
    You must respond **only** with valid JSON that exactly matches the `SchemaMappings` model:
    
    - The top-level object must have a key `"fields"` containing a list.
    - Each item in the list must be an object with:
        - `"input_field"` (optional string) — the field name from the file header.
        - `"mapped_field"` (required string) — the corresponding backend field name.
    
    Do **not** include any markdown, text, or code fences. Respond **only** with JSON.
    
    Example of valid response:
    
    {
        "fields": [
            {"input_field": "RefDes", "mapped_field": "reference"},
            {"input_field": "Value", "mapped_field": "value"},
            {"input_field": "Qty", "mapped_field": "quantity"},
            {"input_field": "Description", "mapped_field": "description"}
        ]
    }
    """
)


async def map_schema(gemini: Gemini, subtype: int, text: str) -> SchemaMappings | None:
    if not SubtypeSchemas.get(subtype):
        logger.debug(f"No subtype mapping required for subtype: {subtype}")
        return
    schema = str(SubtypeSchemas[subtype].model_json_schema())
    prompt = format_instructions(
        f"""
        {schema_mapper_instructions}
        
        Here is the backend schema for this filetype:
        
        {schema}
        
        Here is the file contents:
        
        {text}
        
        """
    )
    return await gemini.generate(
        prompt=prompt,
        instructions=schema_mapper_instructions,
        response_model=SchemaMappings
    )
