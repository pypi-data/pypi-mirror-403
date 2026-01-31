import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Type

from google.genai.types import File as GeminiFile

from mfcli.client.gemini import GeminiFileEntity
from mfcli.constants.file_types import FileSubtypes
from mfcli.models.bom import BOMSchema
from mfcli.models.file import File
from mfcli.models.file_docket import FileDocketEntry
from mfcli.pipeline.analysis.generators.bom.bom import BOMGenerator
from mfcli.pipeline.analysis.generators.debug_setup.debug_setup import DSCheatSheetGenerator
from mfcli.pipeline.analysis.generators.functional_blocks.functional_blocks import (
    extract_functional_blocks_from_file,
    FBCheatSheetGenerator
)
from mfcli.pipeline.analysis.generators.generator_base import GeneratorBase
from mfcli.pipeline.analysis.generators.mcu.mcu import MCUCheatSheetGenerator
from mfcli.pipeline.analysis.generators.mcu_errata.mcu_errata import ErrataCheatSheetGenerator
from mfcli.pipeline.analysis.generators.schematic.schematic import SchematicCheatSheetGenerator
from mfcli.pipeline.analysis.generators.summary.summary import SummaryCheatSheetGenerator
from mfcli.pipeline.run_context import PipelineRunContext
from mfcli.utils.directory_manager import app_dirs
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)

FileSubtypeGeneratorMap: Dict[FileSubtypes, List[Type[GeneratorBase]]] = {
    FileSubtypes.ERRATA: [ErrataCheatSheetGenerator],
    FileSubtypes.MCU_DATASHEET: [MCUCheatSheetGenerator],
    FileSubtypes.SCHEMATIC: [DSCheatSheetGenerator, SchematicCheatSheetGenerator],
    FileSubtypes.USER_GUIDE: [SummaryCheatSheetGenerator],
    FileSubtypes.REFERENCE_MANUAL: [SummaryCheatSheetGenerator]
}

# Mapping of generator classes to friendly output names
GeneratorNameMap: Dict[Any, str] = {
    ErrataCheatSheetGenerator: "mcu_errata",
    MCUCheatSheetGenerator: "mcu",
    DSCheatSheetGenerator: "debug_setup",
    SchematicCheatSheetGenerator: "schematic",
    FBCheatSheetGenerator: "functional_blocks",
    SummaryCheatSheetGenerator: "summary"
}


class Generator:
    def __init__(self, context: PipelineRunContext, processed_file_types: set[str] = None):
        self._context = context
        self._processed_file_types = processed_file_types or set()

    @staticmethod
    def _create_cheat_sheet_json_file(file_path: str, cheat_sheet_data: Dict) -> str:
        # Ensure parent directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8', errors='replace') as jsonfile:
            data = json.dumps(cheat_sheet_data, indent=2, ensure_ascii=False)
            jsonfile.write(data)
            return data

    def _add_to_file_docket(self, file_name: str, file_path: str, vectorize: bool, sub_type: str):
        entry = FileDocketEntry(
            name=file_name,
            path=str(file_path),
            vectorize=vectorize,
            sub_type=sub_type
        )
        self._context.docket.add(entry)

    def _file_subtype_query(self, subtype: FileSubtypes):
        return (
            self._context.db.query(File)
            .filter(File.pipeline_run_id == self._context.run.id)
            .filter(File.sub_type == subtype)
            .filter(File.is_datasheet == 0)
        )

    def _query_first_file_subtype(self, subtype: FileSubtypes) -> File | None:
        return self._file_subtype_query(subtype).first()

    def _query_all_file_subtype(self, subtype: FileSubtypes) -> List[File]:
        return self._file_subtype_query(subtype).all()

    @staticmethod
    def _create_bom_csv(file_path: str, bom_entries: List[Dict]):
        # Ensure parent directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        columns = list(BOMSchema.model_fields.keys())
        with open(file_path, "w", newline="", encoding="utf-8", errors="ignore") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(bom_entries)

    def _vectorize_bom_csv(self, file_path: str):
        with open(file_path, "r") as f:
            self._context.vectorizer.vectorize_text_content(f.read(), "bom.csv", "BOM")

    def _get_gemini_file(self, file: File) -> GeminiFile | None:
        if not self._context.gemini_file_cache.get(file.gemini_file_id):
            logger.warn(f"No Gemini file found for file: {file.id}")
            return
        return self._context.gemini_file_cache[file.gemini_file_id]

    async def _generate_bom(self):
        bom_file = self._query_first_file_subtype(FileSubtypes.BOM)
        if bom_file:
            return
        logger.info("Generation BOM")
        generator = BOMGenerator(self._context.gemini)
        schematic_file = self._query_first_file_subtype(FileSubtypes.SCHEMATIC)
        if not schematic_file:
            return
        gemini_file = self._get_gemini_file(schematic_file)
        if not gemini_file:
            return
        bom_entries = await generator.generate(gemini_file)
        file_path = app_dirs.generated_files_dir / "bom.csv"
        self._create_bom_csv(file_path, bom_entries)
        if self._context.config.vectorize_hw_files:
            self._vectorize_bom_csv(file_path)
        self._add_to_file_docket("bom.csv", file_path, self._context.config.vectorize_hw_files, "BOM")

    @staticmethod
    def _get_generator_name(generator_type: Any) -> str:
        """Get the friendly name for a generator class."""
        return GeneratorNameMap.get(generator_type, generator_type.__name__.lower())

    def _get_cs_vectorization_setting(self, cs_type: Any) -> bool:
        vectorize_config = self._context.config.vectorize_cheat_sheets_config
        should_vectorize = False
        if cs_type == ErrataCheatSheetGenerator:
            should_vectorize = vectorize_config.vectorize_errata
        elif cs_type == MCUCheatSheetGenerator:
            should_vectorize = vectorize_config.vectorize_mcu
        elif cs_type == DSCheatSheetGenerator:
            should_vectorize = vectorize_config.vectorize_debug_setup
        elif cs_type == FBCheatSheetGenerator:
            should_vectorize = vectorize_config.vectorize_functional_blocks
        return should_vectorize

    def _get_gemini_files_from_pdf(self, file: File) -> List[GeminiFile]:
        if not file.pdf_parts:
            return [self._get_gemini_file(file)]
        return [self._get_gemini_file(part) for part in file.pdf_parts]

    async def _generate_functional_blocks(self):
        # TODO: HANDLE CASE OF MULTIPLE SCHEMATIC/USER GUIDES/NETLISTS
        schematic = self._query_first_file_subtype(FileSubtypes.SCHEMATIC)
        schematic_files = self._get_gemini_files_from_pdf(schematic) if schematic else None
        user_guide = self._query_first_file_subtype(FileSubtypes.USER_GUIDE)
        user_guide_files = self._get_gemini_files_from_pdf(user_guide) if user_guide else None

        # TODO: QUERY DIFFERENT NETLISTS
        netlist = self._query_first_file_subtype(FileSubtypes.PROTEL_ALTIUM)

        # Upload netlist to Gemini because it's not a PDF, hasn't been uploaded yet
        netlist_file = None
        if netlist:
            netlist_gemini_file_meta = GeminiFileEntity(
                path=Path(netlist.path),
                mime_type="text/plain"
            )
            netlist_file = await self._context.gemini.upload(netlist_gemini_file_meta)

        if schematic_files or user_guide_files or netlist_file:
            logger.info("Generating functional blocks cheat sheet")

        # Generate functional blocks from uploaded files
        block_data = await extract_functional_blocks_from_file(
            db=self._context.db,
            pipeline_run=self._context.run,
            gemini=self._context.gemini,
            schematic_files=schematic_files,
            user_guide_files=user_guide_files,
            netlist_file=netlist_file
        )

        # Create cheat sheet JSON file
        generator_name = self._get_generator_name(FBCheatSheetGenerator)
        file_name = f"{schematic.name}_{generator_name}_cheat_sheet.json"
        file_path = app_dirs.cheat_sheets_dir / file_name
        text = self._create_cheat_sheet_json_file(file_path, block_data)

        # Vectorize file and add to file docket
        self._vectorize_and_add_to_docket(FBCheatSheetGenerator, file_path, file_name, text)

        # Commit functional blocks to DB
        self._context.db.commit()

    def _vectorize_and_add_to_docket(self, cs_type: Any, file_path: str, file_name: str, text: str):
        logger.debug(f"Vectorizing and adding cheat sheet to docket: {file_name}")
        should_vectorize = self._get_cs_vectorization_setting(cs_type)
        logger.debug(f"Should vectorize: {should_vectorize}")
        if should_vectorize:
            logger.debug(f"Vectorizing cheat sheet: {file_name}")
            self._context.vectorizer.vectorize_text_content(text, file_name, "CHEAT_SHEET")
        logger.debug(f"Adding cheat sheet to docket: {file_name}")
        self._add_to_file_docket(file_name, file_path, should_vectorize, "CHEAT_SHEET")

    async def _generate_for_subtype(self, subtype: FileSubtypes, generators: List[Type[GeneratorBase]]):
        files = self._query_all_file_subtype(subtype)
        for file in files:
            gemini_files = self._get_gemini_files_from_pdf(file)
            if not gemini_files:
                continue
            for generator in generators:
                gen = generator(self._context, file, gemini_files)
                generator_name = self._get_generator_name(generator)
                try:
                    logger.info(f"Generating {generator_name} cheat sheet")
                    cheat_sheet_data = await gen.generate()
                    if not cheat_sheet_data:
                        continue
                    file_name = f"{file.name}_{generator_name}_cheat_sheet.json"
                    file_path = app_dirs.cheat_sheets_dir / file_name
                    text = self._create_cheat_sheet_json_file(file_path, cheat_sheet_data)
                    self._vectorize_and_add_to_docket(generator, file_path, file_name, text)
                except Exception as e:
                    logger.exception(e)
                    logger.error(f"Error generating cheat sheet from {generator_name}")

    async def generate_cheat_sheets(self):
        # Only generate BOM if schematic was processed
        if "SCHEMATIC" in self._processed_file_types:
            logger.info("Generating BOM (schematic was processed)")
            try:
                await self._generate_bom()
            except Exception as e:
                logger.exception(e)
                logger.error(f"Error generating BOM: {self._context.run.id}")
        else:
            logger.info("Skipping BOM generation (schematic not processed)")
        
        # Only generate functional blocks if schematic, user guide, or netlist was processed
        netlist_types = {"PROTEL_ALTIUM", "KICAD_LEGACY_NET", "KICAD_SPICE", "PADS", "EDIF"}
        should_generate_fb = (
            "SCHEMATIC" in self._processed_file_types or
            "USER_GUIDE" in self._processed_file_types or
            any(nt in self._processed_file_types for nt in netlist_types)
        )
        
        if should_generate_fb:
            logger.info("Generating functional blocks (schematic/user guide/netlist was processed)")
            try:
                await self._generate_functional_blocks()
            except Exception as e:
                logger.exception(e)
                logger.error(f"Error generating functional blocks: {self._context.run.id}")
        else:
            logger.info("Skipping functional blocks generation (no relevant files processed)")
        
        # Generate cheat sheets for processed file types only
        for subtype, generators in FileSubtypeGeneratorMap.items():
            if subtype.name in self._processed_file_types:
                logger.info(f"Generating cheat sheets for {subtype.name} (file was processed)")
                await self._generate_for_subtype(subtype, generators)
            else:
                logger.info(f"Skipping cheat sheet generation for {subtype.name} (file not processed)")
