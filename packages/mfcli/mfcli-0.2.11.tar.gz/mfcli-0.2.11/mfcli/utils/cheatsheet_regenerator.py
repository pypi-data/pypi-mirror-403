"""
Utility for regenerating specific cheat sheets.
Allows forcing regeneration of cheat sheets without running the full pipeline.
"""
import asyncio
from pathlib import Path
from typing import List, Type, Optional

from google.genai.types import File as GeminiFile

from mfcli.client.gemini import Gemini, GeminiFileEntity
from mfcli.constants.file_types import FileSubtypes
from mfcli.models.file import File
from mfcli.models.pipeline_run import PipelineRun
from mfcli.models.project import Project
from mfcli.models.project_metadata import ProjectConfig
from mfcli.pipeline.analysis.generators.debug_setup.debug_setup import DSCheatSheetGenerator
from mfcli.pipeline.analysis.generators.functional_blocks.functional_blocks import (
    extract_functional_blocks_from_file,
    FBCheatSheetGenerator
)
from mfcli.pipeline.analysis.generators.generator import Generator, GeneratorNameMap
from mfcli.pipeline.analysis.generators.generator_base import GeneratorBase
from mfcli.pipeline.analysis.generators.mcu.mcu import MCUCheatSheetGenerator
from mfcli.pipeline.analysis.generators.mcu_errata.mcu_errata import ErrataCheatSheetGenerator
from mfcli.pipeline.analysis.generators.schematic.schematic import SchematicCheatSheetGenerator
from mfcli.pipeline.analysis.generators.summary.summary import SummaryCheatSheetGenerator
from mfcli.pipeline.run_context import PipelineRunContext
from mfcli.utils.datasheet_vectorizer import DatasheetVectorizer
from mfcli.utils.directory_manager import app_dirs
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)

# Map user-friendly cheat sheet names to generator classes and file subtypes
CHEATSHEET_TYPE_MAP = {
    "mcu": {
        "generators": [MCUCheatSheetGenerator],
        "subtypes": [FileSubtypes.MCU_DATASHEET],
        "description": "MCU datasheet cheat sheets"
    },
    "errata": {
        "generators": [ErrataCheatSheetGenerator],
        "subtypes": [FileSubtypes.ERRATA],
        "description": "MCU errata cheat sheets"
    },
    "debug_setup": {
        "generators": [DSCheatSheetGenerator],
        "subtypes": [FileSubtypes.SCHEMATIC],
        "description": "Debug setup cheat sheets from schematics"
    },
    "schematic": {
        "generators": [SchematicCheatSheetGenerator],
        "subtypes": [FileSubtypes.SCHEMATIC],
        "description": "Schematic analysis cheat sheets"
    },
    "functional_blocks": {
        "generators": [FBCheatSheetGenerator],
        "subtypes": [FileSubtypes.SCHEMATIC, FileSubtypes.USER_GUIDE],
        "description": "Functional block cheat sheets"
    },
    "summary": {
        "generators": [SummaryCheatSheetGenerator],
        "subtypes": [FileSubtypes.USER_GUIDE, FileSubtypes.REFERENCE_MANUAL],
        "description": "Summary cheat sheets for user guides and reference manuals"
    }
}


class CheatSheetRegenerator:
    """Handles regeneration of specific cheat sheet types."""
    
    def __init__(self, db: Session, config: ProjectConfig):
        self.db = db
        self.config = config
        self.gemini = Gemini()
        self.vectorizer = DatasheetVectorizer(config.name)
        
    def _get_latest_pipeline_run(self) -> Optional[PipelineRun]:
        """Get the most recent successful pipeline run."""
        # First get the project from the database using the project name
        project = self.db.query(Project).filter(Project.name == self.config.name).first()
        if not project:
            logger.error(f"Project '{self.config.name}' not found in database")
            return None
        
        return (
            self.db.query(PipelineRun)
            .filter(PipelineRun.project_id == project.id)
            .order_by(PipelineRun.created_at.desc())
            .first()
        )
    
    def _get_gemini_file_from_db_file(self, file: File) -> Optional[GeminiFile]:
        """Retrieve or reconstruct Gemini file reference from database file."""
        if file.gemini_file_id:
            try:
                return self.gemini.client.files.get(file.gemini_file_id)
            except Exception as e:
                logger.warning(f"Could not retrieve Gemini file {file.gemini_file_id}: {e}")
        return None
    
    def _get_gemini_files_from_pdf(self, file: File) -> List[GeminiFile]:
        """Get Gemini files for a PDF, handling PDF parts if they exist."""
        if not file.pdf_parts:
            gemini_file = self._get_gemini_file_from_db_file(file)
            return [gemini_file] if gemini_file else []
        
        gemini_files = []
        for part in file.pdf_parts:
            gemini_file = self._get_gemini_file_from_db_file(part)
            if gemini_file:
                gemini_files.append(gemini_file)
        return gemini_files
    
    def _create_context(self, pipeline_run: PipelineRun, gemini_file_cache: dict) -> PipelineRunContext:
        """Create a minimal pipeline context for regeneration."""
        from mfcli.models.file_docket import FileDocket
        
        return PipelineRunContext(
            db=self.db,
            pipeline_run=pipeline_run,
            gemini=self.gemini,
            gemini_file_cache=gemini_file_cache,
            docket=FileDocket(),
            config=self.config,
            vectorizer=self.vectorizer
        )
    
    async def _regenerate_functional_blocks(self, pipeline_run: PipelineRun):
        """Special handling for functional blocks which uses multiple file types."""
        logger.info("Regenerating functional blocks cheat sheet")
        
        # Query files
        schematic = (
            self.db.query(File)
            .filter(File.pipeline_run_id == pipeline_run.id)
            .filter(File.sub_type == FileSubtypes.SCHEMATIC)
            .filter(File.is_datasheet == 0)
            .first()
        )
        user_guide = (
            self.db.query(File)
            .filter(File.pipeline_run_id == pipeline_run.id)
            .filter(File.sub_type == FileSubtypes.USER_GUIDE)
            .filter(File.is_datasheet == 0)
            .first()
        )
        netlist = (
            self.db.query(File)
            .filter(File.pipeline_run_id == pipeline_run.id)
            .filter(File.sub_type == FileSubtypes.PROTEL_ALTIUM)
            .filter(File.is_datasheet == 0)
            .first()
        )
        
        if not (schematic or user_guide or netlist):
            logger.warning("No schematic, user guide, or netlist found for functional blocks generation")
            return
        
        schematic_files = self._get_gemini_files_from_pdf(schematic) if schematic else None
        user_guide_files = self._get_gemini_files_from_pdf(user_guide) if user_guide else None
        
        # Upload netlist to Gemini if present
        netlist_file = None
        if netlist:
            netlist_gemini_file_meta = GeminiFileEntity(
                path=Path(netlist.path),
                mime_type="text/plain"
            )
            netlist_file = await self.gemini.upload(netlist_gemini_file_meta)
        
        # Generate functional blocks
        block_data = await extract_functional_blocks_from_file(
            db=self.db,
            pipeline_run=pipeline_run,
            gemini=self.gemini,
            schematic_files=schematic_files,
            user_guide_files=user_guide_files,
            netlist_file=netlist_file
        )
        
        # Create cheat sheet file
        if schematic:
            file_name = f"{schematic.name}_functional_blocks_cheat_sheet.json"
        elif user_guide:
            file_name = f"{user_guide.name}_functional_blocks_cheat_sheet.json"
        else:
            file_name = "functional_blocks_cheat_sheet.json"
            
        file_path = app_dirs.cheat_sheets_dir / file_name
        text = Generator._create_cheat_sheet_json_file(str(file_path), block_data)
        
        # Vectorize if configured
        if self.config.vectorize_cheat_sheets_config.vectorize_functional_blocks:
            logger.info(f"Vectorizing {file_name}")
            self.vectorizer.vectorize_text_content(text, file_name, "CHEAT_SHEET")
        
        self.db.commit()
        logger.info(f"Successfully regenerated functional blocks cheat sheet: {file_name}")
    
    async def _regenerate_for_generator(
        self,
        pipeline_run: PipelineRun,
        generator_class: Type[GeneratorBase],
        subtype: FileSubtypes
    ):
        """Regenerate cheat sheets for a specific generator and file subtype."""
        generator_name = GeneratorNameMap.get(generator_class, generator_class.__name__)
        logger.info(f"Regenerating {generator_name} cheat sheets for {subtype.name} files")
        
        # Query files - don't filter by is_datasheet for schematic subtypes
        query = (
            self.db.query(File)
            .filter(File.pipeline_run_id == pipeline_run.id)
            .filter(File.sub_type == subtype)
        )
        
        # Only filter out datasheets for non-schematic types
        if subtype != FileSubtypes.SCHEMATIC:
            query = query.filter(File.is_datasheet == 0)
        
        files = query.all()
        
        if not files:
            # Provide more helpful debugging info
            all_files = self.db.query(File).filter(File.pipeline_run_id == pipeline_run.id).all()
            logger.warning(f"No {subtype.name} files found for {generator_name} generation")
            logger.info(f"Pipeline run {pipeline_run.id} has {len(all_files)} total files")
            if all_files:
                logger.info(f"Available file types: {set(f.sub_type for f in all_files if f.sub_type)}")
            else:
                logger.info("No files were processed in the most recent pipeline run.")
                logger.info("The 'regenerate' command works with files that have already been processed.")
                logger.info("Please run 'mfcli run' first to process your files, then use 'mfcli regenerate' to regenerate cheat sheets.")
            return
        
        gemini_file_cache = {}
        for file in files:
            gemini_files = self._get_gemini_files_from_pdf(file)
            if not gemini_files:
                logger.warning(f"Could not retrieve Gemini files for {file.name}")
                continue
            
            # Cache Gemini files
            for gf in gemini_files:
                if gf:
                    gemini_file_cache[gf.name] = gf
            
            # Create context and generator
            context = self._create_context(pipeline_run, gemini_file_cache)
            gen = generator_class(context, file, gemini_files)
            
            try:
                cheat_sheet_data = await gen.generate()
                if not cheat_sheet_data:
                    logger.warning(f"No data generated for {file.name}")
                    continue
                
                file_name = f"{file.name}_{generator_name}_cheat_sheet.json"
                file_path = app_dirs.cheat_sheets_dir / file_name
                text = Generator._create_cheat_sheet_json_file(str(file_path), cheat_sheet_data)
                
                # Determine if we should vectorize
                should_vectorize = self._should_vectorize(generator_class)
                if should_vectorize:
                    logger.info(f"Vectorizing {file_name}")
                    self.vectorizer.vectorize_text_content(text, file_name, "CHEAT_SHEET")
                
                logger.info(f"Successfully regenerated cheat sheet: {file_name}")
            except Exception as e:
                logger.exception(e)
                logger.error(f"Error regenerating {generator_name} cheat sheet for {file.name}")
    
    def _should_vectorize(self, generator_class: Type[GeneratorBase]) -> bool:
        """Check if cheat sheets from this generator should be vectorized."""
        vectorize_config = self.config.vectorize_cheat_sheets_config
        
        if generator_class == ErrataCheatSheetGenerator:
            return vectorize_config.vectorize_errata
        elif generator_class == MCUCheatSheetGenerator:
            return vectorize_config.vectorize_mcu
        elif generator_class == DSCheatSheetGenerator:
            return vectorize_config.vectorize_debug_setup
        elif generator_class == FBCheatSheetGenerator:
            return vectorize_config.vectorize_functional_blocks
        
        return False
    
    async def regenerate(self, cheatsheet_type: str) -> bool:
        """
        Regenerate cheat sheets for the specified type.
        
        Args:
            cheatsheet_type: Type of cheat sheet to regenerate (mcu, errata, debug_setup, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        if cheatsheet_type not in CHEATSHEET_TYPE_MAP:
            logger.error(f"Unknown cheat sheet type: {cheatsheet_type}")
            logger.info(f"Valid types: {', '.join(CHEATSHEET_TYPE_MAP.keys())}")
            return False
        
        # Get latest pipeline run
        pipeline_run = self._get_latest_pipeline_run()
        if not pipeline_run:
            logger.error("No pipeline runs found. Please run 'mfcli run' first.")
            return False
        
        logger.info(f"Using pipeline run {pipeline_run.id} from {pipeline_run.created_at}")
        
        config = CHEATSHEET_TYPE_MAP[cheatsheet_type]
        logger.info(f"Regenerating {config['description']}")
        
        try:
            # Special handling for functional blocks
            if cheatsheet_type == "functional_blocks":
                await self._regenerate_functional_blocks(pipeline_run)
            else:
                # Standard generator-based regeneration
                generators = config["generators"]
                subtypes = config["subtypes"]
                
                for generator in generators:
                    for subtype in subtypes:
                        await self._regenerate_for_generator(pipeline_run, generator, subtype)
            
            return True
        except Exception as e:
            logger.exception(e)
            logger.error(f"Failed to regenerate {cheatsheet_type} cheat sheets")
            return False


async def generate_from_file(config: ProjectConfig, cheatsheet_type: str, file_path: Path):
    """
    Generate cheat sheet directly from a file without database lookup.
    
    Args:
        config: Project configuration
        cheatsheet_type: Type of cheat sheet to generate
        file_path: Path to the file to process
    """
    # If file doesn't exist at specified path, check in design folder
    if not file_path.exists():
        design_path = app_dirs.design_dir / file_path.name
        if design_path.exists():
            logger.info(f"File found in design folder: {design_path}")
            file_path = design_path
        else:
            logger.error(f"File not found: {file_path}")
            logger.info(f"Also checked in design folder: {design_path}")
            return False
    
    if cheatsheet_type not in CHEATSHEET_TYPE_MAP:
        logger.error(f"Unknown cheat sheet type: {cheatsheet_type}")
        logger.info(f"Valid types: {', '.join(CHEATSHEET_TYPE_MAP.keys())}")
        return False
    
    logger.info(f"Generating {cheatsheet_type} cheat sheet from file: {file_path}")
    
    # Initialize Gemini and upload file
    gemini = Gemini()
    vectorizer = DatasheetVectorizer(config.name)
    
    # Determine mime type based on file extension
    ext = file_path.suffix.lower()
    if ext == '.pdf':
        mime_type = "application/pdf"
    elif ext in ['.sch', '.kicad_sch']:
        mime_type = "text/plain"
    else:
        mime_type = "application/octet-stream"
    
    try:
        # Upload file to Gemini
        logger.info(f"Uploading file to Gemini: {file_path.name}")
        gemini_file_entity = GeminiFileEntity(path=file_path, mime_type=mime_type)
        gemini_file = await gemini.upload(gemini_file_entity)
        
        # Get generator configuration
        cheat_config = CHEATSHEET_TYPE_MAP[cheatsheet_type]
        generators = cheat_config["generators"]
        
        # Create a minimal context with all required attributes
        from mfcli.models.file_docket import FileDocket
        
        # Create a mock database session (read-only, won't commit anything)
        db = Session()
        
        # Create a mock pipeline run
        mock_run = type('PipelineRun', (), {'id': 0})()
        
        # Create a complete mock context
        context = type('Context', (), {
            'gemini': gemini,
            'config': config,
            'vectorizer': vectorizer,
            'db': db,
            'run': mock_run,
            'gemini_file_cache': {gemini_file.name: gemini_file},
            'docket': FileDocket()
        })()
        
        # Create a mock file object
        mock_file = type('File', (), {
            'name': file_path.stem,
            'path': str(file_path),
            'gemini_file_id': gemini_file.name
        })()
        
        # Generate cheat sheets
        for generator_class in generators:
            generator_name = GeneratorNameMap.get(generator_class, generator_class.__name__)
            logger.info(f"Generating {generator_name} cheat sheet")
            
            try:
                gen = generator_class(context, mock_file, [gemini_file])
                cheat_sheet_data = await gen.generate()
                
                if not cheat_sheet_data:
                    logger.warning(f"No data generated")
                    continue
                
                file_name = f"{file_path.stem}_{generator_name}_cheat_sheet.json"
                output_path = app_dirs.cheat_sheets_dir / file_name
                text = Generator._create_cheat_sheet_json_file(str(output_path), cheat_sheet_data)
                
                # Vectorize if configured
                vectorize_config = config.vectorize_cheat_sheets_config
                should_vectorize = False
                if generator_class == ErrataCheatSheetGenerator:
                    should_vectorize = vectorize_config.vectorize_errata
                elif generator_class == MCUCheatSheetGenerator:
                    should_vectorize = vectorize_config.vectorize_mcu
                elif generator_class == DSCheatSheetGenerator:
                    should_vectorize = vectorize_config.vectorize_debug_setup
                elif generator_class == FBCheatSheetGenerator:
                    should_vectorize = vectorize_config.vectorize_functional_blocks
                
                if should_vectorize:
                    logger.info(f"Vectorizing {file_name}")
                    vectorizer.vectorize_text_content(text, file_name, "CHEAT_SHEET")
                
                logger.info(f"Successfully generated cheat sheet: {file_name}")
                
            except Exception as e:
                logger.exception(e)
                logger.error(f"Error generating {generator_name} cheat sheet")
                return False
        
        return True
        
    except Exception as e:
        logger.exception(e)
        logger.error(f"Failed to generate cheat sheet from file: {file_path}")
        return False


def regenerate_cheatsheet(config: ProjectConfig, cheatsheet_type: str, file_path: Path = None):
    """
    Main entry point for cheat sheet regeneration.
    
    Args:
        config: Project configuration
        cheatsheet_type: Type of cheat sheet to regenerate or 'all' for all types
        file_path: Optional path to specific file to process (bypasses database)
    """
    # If a specific file is provided, generate directly from it
    if file_path:
        asyncio.run(generate_from_file(config, cheatsheet_type, file_path))
        return
    
    # Otherwise, use database records from previous run
    db = Session()
    try:
        regenerator = CheatSheetRegenerator(db, config)
        
        if cheatsheet_type == "all":
            logger.info("Regenerating all cheat sheet types")
            for cs_type in CHEATSHEET_TYPE_MAP.keys():
                asyncio.run(regenerator.regenerate(cs_type))
        else:
            asyncio.run(regenerator.regenerate(cheatsheet_type))
    finally:
        db.close()


def list_cheatsheet_types():
    """Print available cheat sheet types."""
    print("\nAvailable cheat sheet types:")
    print("=" * 80)
    for cs_type, config in CHEATSHEET_TYPE_MAP.items():
        print(f"  {cs_type:20} - {config['description']}")
    print("\nUse 'all' to regenerate all cheat sheet types.")
    print()
