import json
import os.path
from pathlib import Path
from typing import Dict, List

from google.genai.types import File as GeminiFile

from mfcli.models.pdf_parts import PDFPart
from mfcli.models.project_metadata import ProjectConfig
from mfcli.pipeline.preprocessors.user_guide import preprocess_user_guide
from mfcli.pipeline.run_context import PipelineRunContext
from mfcli.utils.datasheet_vectorizer import DatasheetVectorizer

from mfcli.agents.tools.general import format_error_for_llm
from mfcli.client.chroma_db import ChromaClient
from mfcli.client.gemini import Gemini, GeminiFileEntity
from mfcli.constants.directory_names import MF_PROJECT_CONFIG_DIR_NAME
from mfcli.constants.file_types import (
    SchemalessFileSubtypes,
    FileTypes,
    FileSubtypes,
    PDFNoVectorizeFileSubtypes,
    SummaryCheatSheetSubtypes
)
from mfcli.crud.file import create_file
from mfcli.crud.pipeline_run import create_pipeline_run
from mfcli.crud.project import get_project_by_name, read_project_config_file
from mfcli.models.file import File
from mfcli.models.file_docket import FileDocket, FileDocketEntry
from mfcli.models.pipeline_run import PipelineRun
from mfcli.models.project import Project
from mfcli.pipeline.analysis.bom_netlist_mapper import map_netlist_to_bom_entries
from mfcli.pipeline.analysis.generators.generator import Generator
from mfcli.pipeline.classifier import get_file_metadata, validate_file
from mfcli.pipeline.data_enricher import enrich_data_for_model
from mfcli.pipeline.extractor import extract_document_text
from mfcli.pipeline.parser import parse_schema
from mfcli.pipeline.schema_mapper import map_schema
from mfcli.pipeline.sub_classifier import FileSubtypeAnalyzer
from mfcli.utils.directory_manager import app_dirs
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session
from mfcli.utils.pdf_splitter import PDFSplitter

logger = get_logger(__name__)


# TODO: IMPROVE get_file_subtype SO IT DOESN'T USE LLM


class PipelineRunner:
    def __init__(self, db: Session, project: Project, project_config: ProjectConfig):
        self._db = db
        self._project = project
        # Use design folder for file ingestion by default
        self.folder_path = str(app_dirs.design_dir)
        self.total_files = 0
        self.successfully_processed = 0
        self.failed_files = 0
        self.skipped_files = 0
        self.errors = []
        self.pipeline_run: PipelineRun | None = None
        self._gemini = Gemini()
        self._gemini_file_cache: Dict[str, GeminiFile] = {}
        self._chroma_db = ChromaClient(project.index_id)
        self._docket = FileDocket()
        self._vectorizer = DatasheetVectorizer(self._chroma_db)
        self._subtype_analyzer = FileSubtypeAnalyzer(self._gemini)
        self._config = project_config
        self._context = PipelineRunContext(
            db=self._db,
            pipeline_run=self.pipeline_run,
            gemini=self._gemini,
            gemini_file_cache=self._gemini_file_cache,
            docket=self._docket,
            config=self._config,
            vectorizer=self._vectorizer
        )
        # Track which file types were actually processed (not skipped) in this run
        self._processed_file_types: set[str] = set()
        # Load existing file docket if it exists
        self._load_existing_docket()
    
    def _load_existing_docket(self):
        """Load existing file docket from JSON file"""
        if app_dirs.file_docket_path and app_dirs.file_docket_path.exists():
            logger.info(f"Loading existing file docket from: {app_dirs.file_docket_path}")
            self._docket.load_from_json(app_dirs.file_docket_path)
        else:
            logger.info("No existing file docket found, starting fresh")

    def _add_to_file_docket(self, file: File):
        if file.is_datasheet:
            vectorize = self._config.vectorize_datasheets
        else:
            vectorize = self._config.vectorize_hw_files
        entry = FileDocketEntry(
            name=file.name,
            path=file.path,
            vectorize=vectorize,
            sub_type=FileSubtypes(file.sub_type).name,
            md5=file.md5,
            is_datasheet=bool(file.is_datasheet)
        )
        self._docket.add(entry)

    def _save_file_docket(self):
        json_data = json.dumps(self._docket.get_entries(), indent=2)
        with open(app_dirs.file_docket_path, "w") as f:
            f.write(json_data)

    def _check_design_folder_has_files(self) -> bool:
        """
        Check if the design folder contains any files.
        Returns True if files exist, False otherwise.
        """
        design_path = Path(self.folder_path)
        
        if not design_path.exists():
            logger.warning(f"Design folder does not exist: {design_path}")
            return False
        
        # Check for any files in the design folder (recursively)
        ignore_dirs = [MF_PROJECT_CONFIG_DIR_NAME]
        for dir_path, dir_names, file_names in os.walk(design_path):
            dir_names[:] = [d for d in dir_names if d not in ignore_dirs]
            if file_names:
                return True
        
        return False

    def _display_empty_design_message(self):
        """
        Display a helpful message when the design folder is empty.
        """
        design_path = Path(self.folder_path)
        
        print(f"\n{'='*70}")
        print(f"DESIGN FOLDER IS EMPTY")
        print(f"{'='*70}")
        print(f"\nThe design folder contains no files to process:")
        print(f"  {design_path}")
        print(f"\nTo run the pipeline, please add critical files to this folder, such as:")
        print(f"  • Bill of Materials (BOM) files")
        print(f"  • Schematics (PDF or other supported formats)")
        print(f"  • MCU/IC user manuals and datasheets")
        print(f"  • Netlist files")
        print(f"  • Reference designs")
        print(f"  • Application notes")
        print(f"  • Any other hardware design documentation")
        print(f"\nOnce you've added your files, run 'mfcli run' again.")
        print(f"{'='*70}\n")
        
        logger.info("Pipeline execution cancelled: design folder is empty")

    async def _gemini_files_upload(self, files: List[File | PDFPart]) -> List[GeminiFile]:
        gemini_files = []
        for file in files:
            logger.debug(f"Checking for {type(file)} Gemini file")
            if file.gemini_file_id in self._gemini_file_cache:
                gemini_files.append(self._gemini_file_cache[file.gemini_file_id])
                continue
            logger.debug(f"Uploading {type(file)} to Gemini API")
            
            # For File objects with MIME type, use GeminiFileEntity to provide MIME type
            # This is important for files like KiCad schematics where Gemini can't auto-detect
            if isinstance(file, File) and hasattr(file, 'mime_type'):
                file_entity = GeminiFileEntity(
                    path=Path(file.path),
                    mime_type=file.mime_type
                )
                gemini_file = await self._gemini.upload(file_entity)
            else:
                # For PDFPart or files without MIME type, use path directly
                gemini_file = await self._gemini.upload(file.path)
            
            self._gemini_file_cache[gemini_file.name] = gemini_file
            file.gemini_file_id = gemini_file.name
            gemini_files.append(gemini_file)
        return gemini_files

    async def _preprocess_pdf(self, file: File, file_path: str, content: bytes):
        logger.debug(f"Uploading file to Gemini: {file_path}")
        splitter = PDFSplitter(file.name, content)
        logger.debug("Splitting PDF head")
        pdf_head_path = splitter.split_pdf_head()
        gemini_pdf_head_file = await self._gemini.upload(pdf_head_path)
        logger.debug(f"Analyzing PDF subtype: {file_path}")
        await self._subtype_analyzer.analyze_pdf(file, gemini_pdf_head_file)

        # Pre-process user guide files which are too big to upload to Gemini normally
        # Extract the table of contents and split PDF into relevant content sections
        # These sections will be used to generate summaries in analysis phase of pipeline
        if file.sub_type in SummaryCheatSheetSubtypes:
            await preprocess_user_guide(
                context=self._context,
                file=file,
                pdf_head=gemini_pdf_head_file,
                content=content,
                splitter=splitter
            )
        else:
            gemini_files = await self._gemini_files_upload([file])
            logger.debug(f"Gemini files: {gemini_files}")

        if self._config.vectorize_hw_files:
            if file.sub_type in PDFNoVectorizeFileSubtypes:
                logger.debug(f"PDF subtype does not require vectorization, skipping")
            else:
                logger.info(f"Chunking and vectorizing PDF: {file_path}")

                # Use Docling to chunk PDF file and then vectorize it
                self._vectorizer.vectorize_file_buf(
                    file_name=file.name,
                    file_bytes=content,
                    purpose=FileSubtypes(file.sub_type).name
                )
        else:
            logger.debug(f"vectorize_hw_files is set to False, skipping")

    async def _preprocess_other_file_types(self, file: File, file_path: str, content: bytes):
        logger.debug(f"File is not a PDF: {file_path}")
        text_content = extract_document_text(file, content)
        logger.debug(f"Analyzing file subtype: {file_path}")

        # Analyze subtype
        await self._subtype_analyzer.analyze_file(file, text_content)

        # Upload schematic files to Gemini for cheat sheet generation
        # These files need to be available in Gemini for analysis
        if file.sub_type == FileSubtypes.SCHEMATIC:
            logger.debug(f"Uploading schematic file to Gemini: {file_path}")
            gemini_files = await self._gemini_files_upload([file])
            logger.debug(f"Gemini files: {gemini_files}")

        if self._config.vectorize_hw_files:
            logger.info(f"Vectorizing file: {file_path}")

            # Vectorize
            self._vectorizer.vectorize_text_content(
                text=text_content,
                file_name=file.name,
                purpose=FileSubtypes(file.sub_type).name,
                additional_metadata={"is_datasheet": file.is_datasheet}
            )

        # Ignore file subtypes that have no schema to parse like schematic files
        if file.sub_type in SchemalessFileSubtypes:
            logger.debug(f"File subtype is in ignore list, not parsing")
        else:
            logger.debug(f"File subtype is not in ignore list, parsing")

            # Map schema
            logger.debug(f"Mapping schema: {file_path}")
            schema_mapping = await map_schema(self._gemini, file.sub_type, text_content)

            # Parse schema from file
            instances = parse_schema(self._db, file, schema_mapping)

            # Enrich data
            await enrich_data_for_model(self._db, self._chroma_db, file.sub_type, instances)

    async def _preprocess_file(self, file_path: str, is_datasheet: bool) -> File:
        logger.debug(f"Initializing Gemini client for pipeline: {self.pipeline_run.id}")

        # Retrieve metadata
        logger.debug(f"Retrieving file metadata: {file_path}")
        metadata, content = get_file_metadata(file_path, is_datasheet)
        logger.debug(f"Metadata retrieved: {file_path}")

        # Validate file
        validate_file(metadata)
        logger.debug(f"File type validated: {file_path}")

        # Create file
        file = create_file(self._db, self.pipeline_run.id, metadata)

        # PDF file pre-processing
        if file.type == FileTypes.PDF:
            await self._preprocess_pdf(file, file_path, content)

        # Other file types pre-processing
        else:
            await self._preprocess_other_file_types(file, file_path, content)

        self._db.commit()
        logger.info(f"Pre-processing complete: {file_path}")
        return file

    async def _run_analysis(self):
        logger.debug(f"Starting analysis for pipeline: {self.pipeline_run.id}")
        
        # Only run netlist-to-BOM mapping if BOM or netlist files were processed
        netlist_types = {"PROTEL_ALTIUM", "KICAD_LEGACY_NET", "KICAD_SPICE", "PADS", "EDIF"}
        should_map_netlist = (
            "BOM" in self._processed_file_types or 
            any(nt in self._processed_file_types for nt in netlist_types)
        )
        
        if should_map_netlist:
            logger.info("Running netlist-to-BOM mapping (BOM or netlist files were processed)")
            map_netlist_to_bom_entries(self._db, self.pipeline_run.id)
        else:
            logger.info("Skipping netlist-to-BOM mapping (no BOM or netlist files processed)")
        
        logger.debug(f"Finished analysis for pipeline: {self.pipeline_run.id}")
        
        # Pass processed file types to generator for conditional generation
        generator = Generator(self._context, self._processed_file_types)
        await generator.generate_cheat_sheets()

    def _check_file_in_docket(self, file_path: str, file_md5: str) -> tuple[bool, bool]:
        """
        Check if file exists in docket and if MD5 matches.
        Returns: (should_process, should_remove_old)
        """
        # Check if file with same path exists in docket
        existing_entry = self._docket.get_by_path(file_path)
        
        if not existing_entry:
            # File not in docket, process it
            return True, False
        
        # File exists in docket, check MD5
        if existing_entry.md5 == file_md5:
            # MD5 matches, skip processing
            logger.info(f"File already processed with matching MD5, skipping: {file_path}")
            return False, False
        
        # MD5 doesn't match, prompt user
        logger.warning(f"File exists in docket but MD5 has changed: {file_path}")
        logger.warning(f"  Old MD5: {existing_entry.md5}")
        logger.warning(f"  New MD5: {file_md5}")
        
        print(f"\n{'='*70}")
        print(f"File has been modified: {Path(file_path).name}")
        print(f"Path: {file_path}")
        print(f"Old MD5: {existing_entry.md5}")
        print(f"New MD5: {file_md5}")
        print(f"{'='*70}")
        response = input("Do you want to delete the old file data and process the new version? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            logger.info(f"User confirmed deletion and reprocessing of: {file_path}")
            return True, True
        else:
            logger.info(f"User declined reprocessing, skipping: {file_path}")
            return False, False

    def _remove_file_from_kb(self, entry: FileDocketEntry):
        """Remove file from knowledge base (ChromaDB)"""
        try:
            collection = self._chroma_db._collection
            results = collection.get()
            
            if not results or not results.get('metadatas'):
                logger.warning(f"No data found in knowledge base to remove for: {entry.name}")
                return
            
            # Find matching chunks for this file
            matching_ids = []
            for idx, metadata in enumerate(results['metadatas']):
                if metadata and metadata.get('file_name') == entry.name:
                    matching_ids.append(results['ids'][idx])
            
            if matching_ids:
                collection.delete(ids=matching_ids)
                logger.info(f"Removed {len(matching_ids)} chunks from knowledge base for: {entry.name}")
            else:
                logger.info(f"No chunks found in knowledge base for: {entry.name}")
                
            # Remove from docket
            self._docket.remove(entry)
            logger.info(f"Removed file from docket: {entry.name}")
            
        except Exception as e:
            logger.error(f"Error removing file from knowledge base: {entry.name}")
            logger.exception(e)

    async def _preprocess_folder(self, folder_path: str | Path, is_datasheet: bool):
        ignore_dirs = [MF_PROJECT_CONFIG_DIR_NAME]
        for dir_path, dir_names, file_names in os.walk(folder_path):
            dir_names[:] = [d for d in dir_names if d not in ignore_dirs]
            for file_name in file_names:
                self.total_files += 1
                file_path = os.path.join(dir_path, file_name)
                
                try:
                    # Get file metadata to check MD5
                    logger.debug(f"Checking file: {file_path}")
                    metadata, _ = get_file_metadata(file_path, is_datasheet)
                    
                    # Check if file should be processed
                    should_process, should_remove_old = self._check_file_in_docket(file_path, metadata.md5)
                    
                    if not should_process:
                        # Skip this file
                        self.skipped_files += 1
                        logger.info(f"Skipping file: {file_path}")
                        continue
                    
                    # If we need to remove old version first
                    if should_remove_old:
                        existing_entry = self._docket.get_by_path(file_path)
                        if existing_entry:
                            logger.info(f"Removing old version from knowledge base: {file_path}")
                            self._remove_file_from_kb(existing_entry)
                    
                    # Process the file
                    logger.info(f"Pre-processing file: {file_path}")
                    file = await self._preprocess_file(file_path, is_datasheet)
                    self.successfully_processed += 1
                    self._add_to_file_docket(file)
                    
                    # Track the file subtype as processed
                    if file.sub_type:
                        self._processed_file_types.add(FileSubtypes(file.sub_type).name)
                    
                except Exception as e:
                    self.failed_files += 1
                    self.errors.append({"file_path": file_path, "error": str(e)})
                    logger.exception(e)
                    logger.error(f"Error processing file: {file_path}")

    def _check_files_in_docket_but_not_in_db(self) -> List[FileDocketEntry]:
        """
        Check if there are files in file_docket.json that don't exist in the database.
        This can happen if the database was deleted but file_docket.json remains.
        Returns list of docket entries that are not in the database.
        """
        if not self._docket._docket.entries:
            return []
        
        missing_files = []
        for entry in self._docket._docket.entries:
            # Check if any file with this MD5 exists in the database
            existing_file = (
                self._db.query(File)
                .filter(File.md5 == entry.md5)
                .filter(File.name == entry.name)
                .first()
            )
            
            if not existing_file:
                # Check if the file still exists on disk
                if Path(entry.path).exists():
                    missing_files.append(entry)
                else:
                    logger.warning(f"File in docket no longer exists on disk: {entry.path}")
        
        return missing_files
    
    def _prompt_quick_add_files(self, missing_files: List[FileDocketEntry]) -> bool:
        """
        Prompt user if they want to quickly add files to knowledge base.
        Returns True if user wants quick add, False otherwise.
        """
        print(f"\n{'='*70}")
        print(f"FILES IN DOCKET BUT NOT IN DATABASE")
        print(f"{'='*70}")
        print(f"\nFound {len(missing_files)} file(s) in file_docket.json that are not in the database.")
        print(f"This can happen if the database was deleted or you moved to a new machine.\n")
        print(f"Files found:")
        for entry in missing_files[:10]:  # Show first 10
            # Get the subtype name safely
            subtype_display = entry.sub_type if entry.sub_type else 'Unknown'
            try:
                # Try to get the enum name for display, but fall back to the string value if not found
                if entry.sub_type and hasattr(FileSubtypes, entry.sub_type):
                    subtype_display = FileSubtypes[entry.sub_type].name
            except (KeyError, AttributeError):
                # If the subtype is not in the enum, just use the string value
                pass
            print(f"  • {entry.name} ({subtype_display})")
        if len(missing_files) > 10:
            print(f"  ... and {len(missing_files) - 10} more")
        
        print(f"\nOptions:")
        print(f"  1. Quick add: Simply vectorize these files to the knowledge base (faster)")
        print(f"  2. Full process: Run the complete analysis pipeline (slower, more thorough)")
        print(f"  3. Skip: Continue with normal pipeline execution")
        print(f"{'='*70}\n")
        
        response = input("Choose an option (1/2/3): ").strip()
        
        if response == '1':
            return True
        elif response == '2':
            # Clear the docket so files will be fully reprocessed
            logger.info("User chose full reprocessing, clearing file docket")
            self._docket = FileDocket()
            return False
        else:
            return False
    
    async def _quick_add_files_to_kb(self, missing_files: List[FileDocketEntry]):
        """
        Quickly add files to knowledge base by vectorizing them without full processing.
        Respects the 'vectorize' flag in file_docket.json - only vectorizes if flag is True.
        Note: Quick-add mode primarily supports PDF files for optimal results.
        """
        print(f"\n{'='*70}")
        print(f"Quick Adding Files to Knowledge Base")
        print(f"{'='*70}\n")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        # File types that should not be vectorized (structured data, not suitable for text extraction)
        skip_extensions = {'.net', '.csv', '.xml', '.json', '.kicad_sch'}
        
        # File types that are schematic or netlist files (don't need vectorization)
        skip_subtypes = {'SCHEMATIC', 'KICAD_LEGACY_NET', 'PROTEL_ALTIUM', 'KICAD_SPICE', 'PADS', 'EDIF', 'BOM'}
        
        for entry in missing_files:
            try:
                # Check if this file should be vectorized according to docket
                if not entry.vectorize:
                    print(f"Skipping (vectorize=false): {entry.name}")
                    logger.info(f"Skipping file (vectorize flag is false): {entry.path}")
                    skipped_count += 1
                    continue
                
                # Check file extension
                file_ext = Path(entry.path).suffix.lower()
                if file_ext in skip_extensions:
                    print(f"Skipping (unsupported for quick-add): {entry.name}")
                    logger.info(f"Skipping file (unsupported extension for quick-add): {entry.path}")
                    skipped_count += 1
                    continue
                
                # Check subtype
                if entry.sub_type in skip_subtypes:
                    print(f"Skipping (subtype not vectorizable): {entry.name}")
                    logger.info(f"Skipping file (subtype {entry.sub_type} doesn't need vectorization): {entry.path}")
                    skipped_count += 1
                    continue
                
                # Only attempt to vectorize PDF files in quick-add mode
                # Other file types may cause async issues
                if file_ext != '.pdf':
                    print(f"Skipping (only PDFs supported in quick-add): {entry.name}")
                    logger.info(f"Skipping non-PDF file in quick-add: {entry.path}")
                    skipped_count += 1
                    continue
                
                print(f"Vectorizing: {entry.name}...")
                logger.info(f"Quick-adding file to knowledge base: {entry.path}")
                
                # Read PDF file and vectorize using Docling
                with open(entry.path, 'rb') as f:
                    content = f.read()
                
                purpose = entry.sub_type if entry.sub_type else "document"
                self._vectorizer.vectorize_file_buf(
                    file_name=entry.name,
                    file_bytes=content,
                    purpose=purpose
                )
                
                success_count += 1
                logger.info(f"Successfully quick-added: {entry.name}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to quick-add file: {entry.name}")
                logger.exception(e)
                print(f"  ❌ Failed: {entry.name} - {str(e)}")
        
        print(f"\n{'='*70}")
        print(f"Quick Add Summary")
        print(f"{'='*70}")
        print(f"Successfully added: {success_count}")
        print(f"Skipped (various reasons): {skipped_count}")
        print(f"Failed: {failed_count}")
        if skipped_count > 0:
            print(f"\nNote: Quick-add only supports PDF files. For full processing of all file types,")
            print(f"      choose option 2 (Full process) next time, or run 'mfcli run' again.")
        print(f"{'='*70}\n")
        
        logger.info(f"Quick-add completed: {success_count} successful, {skipped_count} skipped, {failed_count} failed")

    async def _identify_and_configure_mcus(self):
        """
        Identify MCUs from BOM/schematic and prompt user for configuration.
        Only runs if MCU configuration doesn't already exist.
        """
        try:
            # Check if MCUs already configured
            if self._config.mcu_config and self._config.mcu_config.primary_mcu:
                logger.info(f"MCUs already configured (primary: {self._config.mcu_config.primary_mcu}), skipping identification")
                return
            
            # Only attempt identification if BOM or MCU datasheet was processed
            if "BOM" not in self._processed_file_types and "MCU_DATASHEET" not in self._processed_file_types:
                logger.info("No BOM or MCU datasheets processed, skipping MCU identification")
                return
            
            logger.info("Identifying microcontrollers from BOM and datasheets")
            
            # Import identification functions
            from mfcli.pipeline.analysis.mcu_identifier import (
                identify_mcus_from_bom,
                identify_mcus_from_datasheets,
                merge_mcu_detections
            )
            from mfcli.utils.mcu_configurator import prompt_mcu_configuration, save_mcu_configuration
            
            # Identify MCUs from both sources
            bom_mcus = identify_mcus_from_bom(self._db, self.pipeline_run.id)
            datasheet_mcus = identify_mcus_from_datasheets(self._db, self.pipeline_run.id)
            
            # Merge detections
            detected_mcus = merge_mcu_detections(bom_mcus, datasheet_mcus)
            
            if not detected_mcus:
                logger.info("No microcontrollers detected in this pipeline run")
                return
            
            # Prompt user for configuration
            mcu_config = prompt_mcu_configuration(detected_mcus)
            
            if mcu_config:
                # Save configuration
                if save_mcu_configuration(mcu_config):
                    # Update in-memory config
                    self._config.mcu_config = mcu_config
                    logger.info(f"MCU configuration saved: primary={mcu_config.primary_mcu}")
            else:
                logger.info("User skipped MCU configuration")
        
        except Exception as e:
            # Don't let MCU configuration errors stop the pipeline
            logger.exception(e)
            logger.error(f"Error during MCU identification: {e}")
            print(f"\n⚠️  Error identifying MCUs: {e}")
            print("    Pipeline will continue without MCU configuration.\n")

    async def run(self):
        try:
            logger.info(f"Starting pipeline for directory: {self.folder_path}")
            
            # Check if design folder has any files
            if not self._check_design_folder_has_files():
                self._display_empty_design_message()
                return
            
            # Check if there are files in docket but not in database
            missing_files = self._check_files_in_docket_but_not_in_db()
            if missing_files:
                if self._prompt_quick_add_files(missing_files):
                    await self._quick_add_files_to_kb(missing_files)
                    print("\n✅ Quick add completed. Files are now in the knowledge base.")
                    print("   You can run 'mfcli run' again if you want to do full processing.\n")
                    return
            
            self.pipeline_run = create_pipeline_run(self._db, self._project)
            self._context.run = self.pipeline_run
            await self._preprocess_folder(self.folder_path, False)
            logger.info(f"Finished pre-processing folder: {self.folder_path}")

            # Run pre-processing on datasheets which were just downloaded
            logger.info(f"Starting pre-processing of datasheets: {app_dirs.data_sheets_dir}")
            await self._preprocess_folder(app_dirs.data_sheets_dir, True)
            logger.info(f"Finished pre-processing of datasheets: {app_dirs.data_sheets_dir}")

            logger.info(f"Preprocessing finished: {self.folder_path}")
            
            # Identify and configure MCUs if not already configured
            await self._identify_and_configure_mcus()
            
            logger.info(f"Running analysis step: {self.folder_path}")
            await self._run_analysis()
            self._db.commit()
            self._save_file_docket()
            report = json.dumps({
                "total_files": self.total_files,
                "successfully_processed": self.successfully_processed,
                "skipped_files": self.skipped_files,
                "failed_files": self.failed_files,
                "errors": self.errors
            })
            logger.info(f"Finished pipeline")
            logger.info(f"Report: {report}")
            
            # Print summary to console
            print(f"\n{'='*70}")
            print(f"Pipeline Execution Summary")
            print(f"{'='*70}")
            print(f"Total files found: {self.total_files}")
            print(f"Successfully processed: {self.successfully_processed}")
            print(f"Skipped (already processed): {self.skipped_files}")
            print(f"Failed: {self.failed_files}")
            print(f"{'='*70}\n")
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error in pipeline: {e}")
            return format_error_for_llm(e)


async def run_with_config(project_config: ProjectConfig):
    with Session() as db:
        project = get_project_by_name(db, project_config.name)
        return await PipelineRunner(db, project, project_config).run()


async def run(project_name: str) -> str:
    """
    The controller agent will call this tool to start the pipeline processing for all the files in a directory.
    :param project_name: The name of the project
    :return: Status of the pipeline run
    """
    with Session() as db:
        project = get_project_by_name(db, project_name)
        project_config = read_project_config_file()
        return await PipelineRunner(db, project, project_config).run()
