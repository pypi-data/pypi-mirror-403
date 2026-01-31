from typing import List

from mfcli.models.functional_blocks import FunctionalBlockMeta, FunctionalBlock, FunctionalBlockComponent
from mfcli.models.pipeline_run import PipelineRun
from mfcli.utils.orm import Session


def create_functional_blocks(
    db: Session,
    pipeline_run: PipelineRun,
    blocks: List[FunctionalBlockMeta]
) -> None:
    db_blocks = []
    for block in blocks:
        db_block = FunctionalBlock(
            name=block.name,
            description=block.description,
            pipeline_run=pipeline_run,
            components=[]
        )
        for component_ref in (block.components or []):
            db_block.components.append(
                FunctionalBlockComponent(ref=component_ref)
            )
        db_blocks.append(db_block)
    db.add_all(db_blocks)
