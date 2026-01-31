from mfcli.models.netlist import NetlistSchema, Netlist, NetlistComponent, NetlistPin


def create_netlist(pipeline_run_id: int, netlist_schema: NetlistSchema) -> Netlist:
    netlist = Netlist(pipeline_run_id=pipeline_run_id)
    for component_schema in netlist_schema.components:
        component = NetlistComponent(
            ref_des=component_schema.ref_des,
            part_number=component_schema.part_number
        )
        netlist.components.append(component)
        for pin_schema in component_schema.pins:
            pin = NetlistPin(
                pin=pin_schema.pin,
                net=pin_schema.net
            )
            component.pins.append(pin)
    return netlist
