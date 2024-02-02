from __future__ import annotations

from attrs import define

from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectionModeEnum,
    IsolationLevelEnum,
)

from cloudshell.cp.cloudstack.entities.network_type import NetworkType
from cloudshell.cp.cloudstack.models.connectivity_action_model import (
    CloudstackConnectivityActionModel,
    SubnetCidrData,
)
from cloudshell.cp.cloudstack.models.resource_config import CloudstackResourceConfig

QS_NAME_PREFIX = "QS"
NETWORK_PREFIX = f"{QS_NAME_PREFIX}_VLAN"


def get_existing_network(action: CloudstackConnectivityActionModel) -> str | None:
    existing_network = (
        action.connection_params.vlan_service_attrs.existing_network
        or action.connection_params.vlan_service_attrs.virtual_network  # deprecated
    )
    return existing_network


def generate_port_group_name_v2(
    *,
    vlan_id: str,
    port_mode: ConnectionModeEnum,
    forged_transmits: bool,
    mac_changes: bool,
    promiscuous_mode: bool,
    exclusive: bool,
) -> str:
    flags = "E" if exclusive else "S"
    flags += "F" if forged_transmits else ""
    flags += "M" if mac_changes else ""
    flags += "P" if promiscuous_mode else ""
    return f"{NETWORK_PREFIX}_{vlan_id}_{port_mode.value}_{flags}"


@define
class NetworkSettings:
    name: str
    existed: bool
    exclusive: bool
    vlan_id: str
    port_mode: ConnectionModeEnum
    promiscuous_mode: bool
    forged_transmits: bool
    mac_changes: bool
    vm_uuid: str
    network_isolation: NetworkType
    subnet: SubnetCidrData | None = None
    zone_id: str | None = None

    @classmethod
    def convert(
        cls,
        action: CloudstackConnectivityActionModel,
        conf: CloudstackResourceConfig,
    ) -> NetworkSettings:
        con_params = action.connection_params
        vlan_service = con_params.vlan_service_attrs

        vlan_id = con_params.vlan_id
        port_mode = con_params.mode
        exclusive = vlan_service.isolation_level is IsolationLevelEnum.EXCLUSIVE
        if (promiscuous_mode := vlan_service.promiscuous_mode) is None:
            promiscuous_mode = None
        if (forged_transmits := vlan_service.forged_transmits) is None:
            forged_transmits = None
        if (mac_changes := vlan_service.mac_changes) is None:
            mac_changes = None

        if name := get_existing_network(action):
            existed = True
        else:
            existed = False
            name = generate_port_group_name_v2(
                vlan_id=vlan_id,
                port_mode=port_mode,
                forged_transmits=forged_transmits,
                mac_changes=mac_changes,
                promiscuous_mode=promiscuous_mode,
                exclusive=exclusive,
            )
        subnet = vlan_service.subnet_cidr
        network_isolation = vlan_service.network_isolation
        return cls(
            name=name,
            existed=existed,
            exclusive=exclusive,
            vlan_id=vlan_id,
            port_mode=port_mode,
            promiscuous_mode=promiscuous_mode,
            forged_transmits=forged_transmits,
            mac_changes=mac_changes,
            vm_uuid=action.custom_action_attrs.vm_uuid,
            network_isolation=network_isolation,
            subnet=subnet,
        )  # type: ignore
