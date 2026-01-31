from mfcli.models.bom import BOM
from mfcli.models.file import File
from mfcli.models.netlist import NetlistComponent, Netlist
from mfcli.utils.logger import get_logger
from mfcli.utils.orm import Session

logger = get_logger(__name__)


def map_netlist_to_bom_entries(db: Session, pipeline_run_id: int):
    logger.debug(f"Mapping netlist to BOM entries for pipeline: {pipeline_run_id}")
    components: list[NetlistComponent] = (
        db.query(NetlistComponent)
        .join(NetlistComponent.netlist)
        .filter(Netlist.pipeline_run_id == pipeline_run_id)
        .all()
    )
    results = (
        db.query(BOM.id, BOM.value)
        .join(BOM.file)
        .filter(File.pipeline_run_id == pipeline_run_id)
        .all()
    )
    bom_value_id_map = {result[1]: result[0] for result in results}
    for component in components:
        if bom_value_id_map.get(component.part_number):
            component.bom_entry_id = bom_value_id_map[component.part_number]
    logger.debug(f"All netlist entries mapped: {pipeline_run_id}")
