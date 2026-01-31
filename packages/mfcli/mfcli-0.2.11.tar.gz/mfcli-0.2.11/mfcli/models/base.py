from sqlalchemy.orm import declarative_base, configure_mappers
from sqlmodel import SQLModel

Base = declarative_base()

import mfcli.models

configure_mappers()

target_metadata = SQLModel.metadata
