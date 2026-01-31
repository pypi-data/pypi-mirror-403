import asyncio
from asyncio import Semaphore
from typing import Dict, Type, List

from google.genai.types import File as GeminiFile
from pydantic import BaseModel

from mfcli.models.file import File
from mfcli.models.netlist import NetlistComponent, NetlistPin
from mfcli.models.schematic_cheatsheet import (
    MCUSummary,
    PinMap,
    BusMap,
    BusDefinition,
    BusDevice,
    PeripheralList,
    PowerSequencing,
    ConstraintsGotchas,
    ConnectorPinouts
)
from mfcli.pipeline.analysis.generators.generator_base import GeneratorBase
from mfcli.pipeline.analysis.generators.schematic.instructions import (
    sch_mcu_summary_instructions,
    sch_pin_map_instructions,
    sch_bus_map_instructions,
    sch_peripheral_list_instructions,
    sch_power_sequencing_instructions,
    sch_constraints_gotchas_instructions,
    sch_connector_pinouts_instructions,
    sch_system_instructions
)
from mfcli.pipeline.run_context import PipelineRunContext
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)

SchematicModelInstructionsMap = {
    MCUSummary: sch_mcu_summary_instructions,
    PinMap: sch_pin_map_instructions,
    BusMap: sch_bus_map_instructions,
    PeripheralList: sch_peripheral_list_instructions,
    PowerSequencing: sch_power_sequencing_instructions,
    ConstraintsGotchas: sch_constraints_gotchas_instructions,
    ConnectorPinouts: sch_connector_pinouts_instructions
}


class SchematicCheatSheetGenerator(GeneratorBase):
    def __init__(self, context: PipelineRunContext, db_file: File, uploads: List[GeminiFile]):
        super().__init__(context, db_file, uploads)
        self._sem = Semaphore(5)

    async def _extract_sch_data(self, model: Type[BaseModel], instructions: str) -> BaseModel:
        """Extract data from schematic using AI."""
        return await self._context.gemini.generate(
            prompt=instructions,
            instructions=sch_system_instructions,
            response_model=model,
            files=self._uploads
        )

    def _enhance_bus_map_with_netlist(self, bus_map: BusMap) -> BusMap:
        """Enhance bus map with netlist data for more accurate device connections."""
        try:
            # Query all netlist components for this pipeline run
            netlist_components = (
                self._context.db.query(NetlistComponent)
                .join(NetlistComponent.netlist)
                .filter(NetlistComponent.netlist.has(pipeline_run_id=self._context.run.id))
                .all()
            )

            if not netlist_components:
                logger.info("No netlist data available for bus map enhancement")
                return bus_map

            # Build a map of nets to components
            net_to_components = {}
            for component in netlist_components:
                for pin in component.pins:
                    if pin.net not in net_to_components:
                        net_to_components[pin.net] = []
                    net_to_components[pin.net].append({
                        'ref_des': component.ref_des,
                        'part_number': component.part_number,
                        'pin': pin.pin
                    })

            # Enhance each bus with netlist data
            for bus in bus_map.buses:
                # Get components connected to bus signal nets
                connected_components = set()
                for signal, net_name in bus.signal_nets.items():
                    if net_name in net_to_components:
                        for comp_info in net_to_components[net_name]:
                            connected_components.add(comp_info['ref_des'])

                # Cross-reference with AI-extracted devices
                for device in bus.devices:
                    # Try to find this device in the netlist
                    if device.ref_des:
                        # Verify device is actually connected to bus signals
                        device_connected = False
                        for component in netlist_components:
                            if component.ref_des == device.ref_des:
                                for pin in component.pins:
                                    if pin.net in bus.signal_nets.values():
                                        device_connected = True
                                        break
                        
                        if not device_connected and device.ref_des in connected_components:
                            logger.warning(
                                f"Device {device.ref_des} listed on bus {bus.bus_name} "
                                f"but netlist shows no connection"
                            )

                # Look for devices connected to bus that AI might have missed
                for ref_des in connected_components:
                    # Check if this device is already in the AI-extracted list
                    if not any(d.ref_des == ref_des for d in bus.devices):
                        # Find the component details
                        for component in netlist_components:
                            if component.ref_des == ref_des:
                                # Add missing device to bus
                                missing_device = BusDevice(
                                    device_name=f"Device {ref_des}",
                                    ref_des=ref_des,
                                    address="",  # Would need AI or further analysis
                                    irq_pin="",
                                    reset_pin="",
                                    enable_pin="",
                                    other_signals={}
                                )
                                bus.devices.append(missing_device)
                                logger.info(
                                    f"Added missing device {ref_des} to bus {bus.bus_name} "
                                    f"from netlist analysis"
                                )
                                break

            logger.info("Bus map enhanced with netlist data")
            return bus_map

        except Exception as e:
            logger.warning(f"Failed to enhance bus map with netlist: {e}")
            return bus_map

    async def generate(self) -> Dict:
        """Generate complete schematic cheat sheet."""
        tasks = []
        
        # Create extraction tasks for all sections
        for model, instructions in SchematicModelInstructionsMap.items():
            tasks.append(self._extract_sch_data(model, instructions))
        
        # Execute all extraction tasks in parallel
        results: list[BaseModel] = await asyncio.gather(*tasks)
        
        # Combine results into single dictionary
        response_dict = {}
        for result in results:
            # Special handling for bus map - enhance with netlist data
            if isinstance(result, BusMap):
                result = self._enhance_bus_map_with_netlist(result)
            
            response_dict.update(result.model_dump())
        
        return {
            "schematic": response_dict
        }
