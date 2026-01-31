import json
from pathlib import Path
from typing import Type

import pandas as pd
from sqlmodel import SQLModel

from mfcli.constants.file_types import FileTypes, FileSubtypes
from mfcli.crud.netlist import create_netlist
from mfcli.models.file import File
from mfcli.models.netlist import Netlist
from mfcli.pipeline.parsers.netlist.kicad_legacy_net import parse_kicad_legacy_net_file
from mfcli.pipeline.parsers.netlist.kicad_spice import parse_kicad_spice_file
from mfcli.pipeline.parsers.netlist.pads import parse_pads_file
from mfcli.pipeline.parsers.netlist.protel import parse_protel_file
from mfcli.pipeline.schema_mapper import SchemaMappings, SubtypeModels
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)


def parse_csv(file_path: str) -> dict:
    logger.debug(f"Parsing CSV: {file_path}")
    df = pd.read_csv(file_path, header='infer', encoding_errors='ignore')
    json_str = df.to_json(orient="records")
    logger.debug(f"CSV parsed: {file_path}")
    return json.loads(json_str)


def _extract_schema_from_csv(
        file: File,
        input_column_field_map: dict[str, str],
        model: Type[SQLModel]
) -> list[SQLModel]:
    rows = parse_csv(file.path)
    model_instances: list[SQLModel] = []
    for row in rows:
        try:
            mapped_data = {}
            for input_col, model_field in input_column_field_map.items():
                if input_col in row:
                    mapped_data[model_field] = row[input_col]
                else:
                    mapped_data[model_field] = None
            instance = model(**mapped_data)
            instance.file_id = file.id
            model_instances.append(instance)
            logger.debug(f"Model parsed from CSV: {instance}")
        except Exception as e:
            logger.warn(e)
    if not model_instances:
        raise ValueError(f"No data could be parsed from this CSV: {file.path}")
    return model_instances


class SchemaParser:
    def __init__(self, db: Session, file: File):
        self._db = db
        self.file = file

    def _parse_with_schema_mappings(
            self,
            model: Type[SQLModel],
            mappings: SchemaMappings
    ) -> list[SQLModel]:
        input_column_field_map = {mapping.input_field: mapping.mapped_field for mapping in mappings.fields}
        logger.debug(f"Model: {model}")
        if self.file.type == FileTypes.CSV:
            return _extract_schema_from_csv(self.file, input_column_field_map, model)
        raise ValueError(f"Unsupported extraction file type: {self.file.type}")

    @staticmethod
    def _is_netlist_file(subtype: FileSubtypes):
        if subtype in [
            FileSubtypes.KICAD_LEGACY_NET,
            FileSubtypes.KICAD_SPICE,
            FileSubtypes.PADS_PCB_ASCII,
            FileSubtypes.PROTEL_ALTIUM
        ]:
            return True
        return False

    def _parse_netlist_file(self, subtype: FileSubtypes, file_path: Path) -> Netlist:
        if subtype == FileSubtypes.KICAD_LEGACY_NET:
            netlist_schema = parse_kicad_legacy_net_file(file_path)
        elif subtype == FileSubtypes.PADS_PCB_ASCII:
            netlist_schema = parse_pads_file(file_path)
        elif subtype == FileSubtypes.KICAD_SPICE:
            netlist_schema = parse_kicad_spice_file(file_path)
        elif subtype == FileSubtypes.PROTEL_ALTIUM:
            netlist_schema = parse_protel_file(file_path)
        else:
            raise ValueError(f"Netlist file has no parser: {self.file.name}")
        netlist = create_netlist(self.file.pipeline_run_id, netlist_schema)
        return netlist

    def _parse_without_schema_mappings(self) -> list[SQLModel]:
        subtype = self.file.sub_type
        file_path = Path(self.file.path)
        if self._is_netlist_file(subtype):
            return [self._parse_netlist_file(subtype, file_path)]
        raise ValueError(f"No parser for file subtype: {self.file.sub_type}")

    def parse(self, mappings: SchemaMappings | None) -> list[SQLModel]:
        logger.debug(f"Extracting schema from file: {self.file.name}")
        if not SubtypeModels.get(self.file.sub_type):
            raise ValueError(f"Cannot find subtype model for subtype: {self.file.sub_type}")
        model: Type[SQLModel] = SubtypeModels.get(self.file.sub_type)
        if mappings:
            instances = self._parse_with_schema_mappings(model, mappings)
        else:
            instances = self._parse_without_schema_mappings()
        self._db.add_all(instances)
        logger.debug(f"File has been successfully parsed")
        return instances


def parse_schema(db: Session, file: File, mappings: SchemaMappings | None) -> list[SQLModel]:
    return SchemaParser(db, file).parse(mappings)
