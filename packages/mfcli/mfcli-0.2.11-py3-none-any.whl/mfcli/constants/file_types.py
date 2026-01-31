from typing import Literal, Dict

from mfcli.constants.base_enum import BaseEnum

FILE_SUBTYPE_UNKNOWN = "UNKNOWN"


class FileTypes(BaseEnum):
    CSV = 1
    ASC = 2
    NET = 3
    CIR = 4
    PDF = 5
    SCH = 6
    KICAD_SCH = 7
    TXT = 8
    RTF = 9
    DOCX = 10
    JPG = 11


class FileSubtypes(BaseEnum):
    BOM = 1
    PADS_PCB_ASCII = 2
    KICAD_LEGACY_NET = 3
    KICAD_SPICE = 4
    SCHEMATIC = 5
    ERRATA = 6
    MCU_DATASHEET = 7
    PROTEL_ALTIUM = 8
    GENERAL_DATASHEET = 9
    UNKNOWN = 10
    USER_GUIDE = 11
    REFERENCE_MANUAL = 12


# PDF subtypes which require summary cheat sheets
SummaryCheatSheetSubtypes: set[FileSubtypes] = {
    FileSubtypes.USER_GUIDE,
    FileSubtypes.REFERENCE_MANUAL
}

# PDF file subtypes that do not require docling text extraction or vectorization (example, schematic files)
PDFNoVectorizeFileSubtypes: set[FileSubtypes] = {
    FileSubtypes.SCHEMATIC
}

# File subtypes that have no schema to parse
SchemalessFileSubtypes: set[FileSubtypes] = {
    FileSubtypes.SCHEMATIC,
    FileSubtypes.ERRATA,
    FileSubtypes.MCU_DATASHEET,
    FileSubtypes.USER_GUIDE,
    FileSubtypes.REFERENCE_MANUAL,
    FileSubtypes.GENERAL_DATASHEET,
    FileSubtypes.UNKNOWN
}

# File subtype names are for use with LLM, validating subtype response

PDFFileSubtypeNames = Literal[
    'SCHEMATIC',
    'ERRATA',
    'MCU_DATASHEET',
    'GENERAL_DATASHEET',
    'USER_GUIDE',
    'REFERENCE_MANUAL',
    'UNKNOWN'
]

OtherFileSubtypeNames = Literal[
    'BOM',
    'PADS_PCB_ASCII',
    'KICAD_LEGACY_NET',
    'KICAD_SPICE',
    'PROTEL_ALTIUM',
    'UNKNOWN'
]

PDFMimeTypes = {
    "application/pdf",
    "application/x-pdf",
    "application/acrobat",
    "applications/vnd.pdf",
    "application/nappdf",
}

SupportedFileTypes = {
    "CSV": {
        "mime_types": {
            "text/csv",
            "text/plain",
            "application/vnd.ms-excel"
        },
        "subtypes": {
            "BOM"
        }
    },
    "ASC": {
        "mime_types": {
            "text/plain"
        },
        "subtypes": {
            "PADS_PCB_ASCII"
        }
    },
    "NET": {
        "mime_types": {
            "text/plain"
        },
        "subtypes": {
            "KICAD_LEGACY_NET",
            "PROTEL_ALTIUM"
        }
    },
    "CIR": {
        "mime_types": {
            "text/plain"
        },
        "subtypes": {
            "KICAD_SPICE"
        }
    },
    "PDF": {
        "mime_types": PDFMimeTypes,
        "subtypes": {
            "SCHEMATIC",
            "ERRATA",
            "MCU_DATASHEET",
            "REFERENCE_MANUAL"
        }
    },
    "SCH": {
        "mime_types": {
            "text/plain"
        },
        "subtypes": {
            "SCHEMATIC"
        }
    },
    "KICAD_SCH": {
        "mime_types": {
            "text/plain"
        },
        "subtypes": {
            "SCHEMATIC"
        }
    },
    "TXT": {
        "mime_types": {
            "text/plain"
        },
        "subtypes": {
            "UNKNOWN"
        }
    },
    "RTF": {
        "mime_types": {
            "application/rtf",
            "text/rtf"
        },
        "subtypes": {
            "UNKNOWN"
        }
    },
    "DOCX": {
        "mime_types": {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        },
        "subtypes": {
            "UNKNOWN"
        }
    },
    "JPG": {
        "mime_types": {
            "image/jpeg",
            "image/jpg"
        },
        "subtypes": {
            "UNKNOWN"
        }
    }
}

# File subtype descriptions (for use in file subtype auto-discovery)

# File subtypes for which we have parsers and do not the LLM to discover subtype
KnownFileSubtypeDescriptions: Dict[SupportedFileTypes, Dict[str, str]] = {
    "KICAD_LEGACY_NET": {
        "name": 'KiCad Legacy Netlist',
        "description": "Older KiCad netlist format containing components, nets, pins, and footprint references using plain text blocks like (comp ...), (net ...), and (pin ...); does not contain SPICE commands or PCB geometry."
    },
    "PROTEL_ALTIUM": {
        "name": "Protel/Altium Designer Netlist",
        "description": "Hierarchical bracketed netlist with components, footprints, and pin-to-net connections using sections like [Component] and [Net]; verbose structure unique to Altium/Protel; not a PCB layout or SPICE file."
    }
}

# Only PDF files
PDFSubtypeDescriptions: Dict[SupportedFileTypes, Dict[str, str]] = {
    "SCHEMATIC": {
        "name": "Schematic",
        "description": "Diagrammatic circuit representation containing symbols, wires, net labels, sheet numbers, and component reference designators; typically PDF or image-based; not a table, netlist, PCB file, or simulation file."
    },
    "ERRATA": {
        "name": "Engineering Errata File",
        "description": "An ERRATA document lists known defects, mistakes, missing features, and silicon bugs in a released product. It is NOT a datasheet, does NOT describe product specifications, and consists of issue-by-issue bullet points with IDs, status, and workarounds. It never contains full electrical characteristics tables, application diagrams, or packaging information."
    },
    "MCU_DATASHEET": {
        "name": "MCU Datasheet",
        "description": "Microcontroller technical reference containing CPU architecture, memory maps, peripheral descriptions, electrical characteristics, pinouts, timing diagrams, and register information; exclusive to microcontrollers."
    },
    "GENERAL_DATASHEET": {
        "name": "General Component Datasheet",
        "description": "Datasheet for non-MCU components such as ICs, sensors, regulators, passives, and connectors, containing electrical specs, pin descriptions, operating conditions, and application circuits; no CPU or register-map content. A general component datasheet is a large, structured document containing electrical specifications, tables, operating ranges, application circuits, diagrams, pinouts, mechanical drawings, and packaging information. It is not a list of defects and does not describe known problems."
    },
    "USER_GUIDE": {
        "name": "User Guide",
        "description": "A practical, instructional document that explains how to use a hardware device, development board, evaluation kit, or module. A user guide focuses on setup, configuration, jumper settings, power requirements, interfaces, connectors, example usage, and safety notes. Unlike a datasheet, it avoids deep electrical specifications, register maps, or silicon details, and instead provides step-by-step procedures, diagrams, block overviews, and usage instructions intended for end users or developers."
    },
    "REFERENCE_MANUAL": {
        "name": "Hardware Reference Manual",
        "description": "A detailed, authoritative technical manual that defines the internal hardware architecture and low-level behavior of a device or system. It provides exhaustive functional descriptions of hardware blocks, registers, memory maps, address spaces, bit fields, timing relationships, and control logic. A hardware reference manual is used by firmware and driver developers for direct hardware interaction. It is not a datasheet, does not focus on electrical specifications or marketing summaries, and is not a step-by-step user guide."
    },
    "UNKNOWN": {
        "name": "Unknown File",
        "description": "File content does not match any known category such as BOM, PCB, netlist, schematic, datasheet, SPICE, or errata; used when insufficient or ambiguous information is present."
    }
}

# Any other files subtypes
OtherFileTypeDescriptions: Dict[SupportedFileTypes, Dict[str, str]] = {
    "BOM": {
        "name": "Bill of Materials (BOM)",
        "description": "Tabular component list containing part numbers, quantities, manufacturers, and descriptions; typically CSV/XLSX rows and columns; does not contain nets, schematic symbols, PCB layout, or SPICE commands."
    },
    "PADS_PCB_ASCII": {
        "name": "PADS ASCII PCB",
        "description": "ASCII export of a PADS PCB layout containing footprints, padstacks, copper geometry, vias, XY coordinates, and board definitions; does not contain schematic symbols, part tables, or SPICE simulation directives."
    },
    "KICAD_LEGACY_NET": {
        "name": "KiCad Legacy Netlist",
        "description": "Older KiCad netlist format containing components, nets, pins, and footprint references using plain text blocks like (comp ...), (net ...), and (pin ...); does not contain SPICE commands or PCB geometry."
    },
    "PROTEL_ALTIUM": {
        "name": "Protel/Altium Designer Netlist",
        "description": "Hierarchical bracketed netlist with components, footprints, and pin-to-net connections using sections like [Component] and [Net]; verbose structure unique to Altium/Protel; not a PCB layout or SPICE file."
    },
    "KICAD_SPICE": {
        "name": "KiCad SPICE Netlist",
        "description": "SPICE circuit simulation file containing directives (.tran, .ac, .dc, .include), models, and device lines (R, C, L, V, I elements); does not contain PCB footprints, tables, or datasheet content."
    },
    "UNKNOWN": {
        "name": "Unknown File",
        "description": "File content does not match any known category such as BOM, PCB, netlist, schematic, datasheet, SPICE, or errata; used when insufficient or ambiguous information is present."
    }
}
