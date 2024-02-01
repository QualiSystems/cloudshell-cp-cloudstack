from __future__ import annotations

import logging
from contextlib import suppress
from functools import cached_property
from itertools import chain
from typing import TYPE_CHECKING, Any

from attrs import define, field

from cloudshell.shell.flows.connectivity.cloud_providers_flow import (
    AbcCloudProviderConnectivityFlow,
    VnicInfo,
)
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectionModeEnum,
    is_remove_action,
    is_set_action,
)

from cloudshell.cp.cloudstack.entities.network import Network
from cloudshell.cp.cloudstack.entities.network_offering import NetworkOfferingType
from cloudshell.cp.cloudstack.entities.network_type import NetworkType
from cloudshell.cp.cloudstack.entities.vm import CloudstackVirtualMachine, Interface
from cloudshell.cp.cloudstack.exceptions import (
    InstanceNotFound,
    NetworkNotFound,
    PortNotFound,
)
from cloudshell.cp.cloudstack.helpers.network_settings_helper import (
    NETWORK_PREFIX,
    NetworkSettings,
)
from cloudshell.cp.cloudstack.helpers.threading import LockHandler
from cloudshell.cp.cloudstack.models.connectivity_action_model import (
    CloudstackConnectivityActionModel,
)
from cloudshell.cp.cloudstack.models.resource_config import CloudstackResourceConfig
from cloudshell.cp.cloudstack.services.cloudstack_api_service import (
    CloudStackAPIService,
)

if TYPE_CHECKING:
    from collections.abc import Collection
    from concurrent.futures import ThreadPoolExecutor

    from cloudshell.cp.core.reservation_info import ReservationInfo

VM_NOT_FOUND_MSG = "VM {} is not found. Skip disconnecting vNIC"
logger = logging.getLogger(__name__)
network_lock = LockHandler()


# switch_lock = LockHandler()


@define(slots=False)
class ConnectivityFlow(AbcCloudProviderConnectivityFlow):
    _api_service: CloudStackAPIService
    _resource_conf: CloudstackResourceConfig
    _reservation_info: ReservationInfo
    _networks: dict[str, Network] = field(init=False, factory=dict)

    def __attrs_post_init__(self):
        self._sandbox_id = self._reservation_info.reservation_id

    def validate_actions(
        self, actions: Collection[CloudstackConnectivityActionModel]
    ) -> None:
        # if switch name not specified in VLAN service or in resource config
        # converter would raise an exception
        _ = [self._get_network_settings(action) for action in actions]

    def pre_connectivity(
        self,
        actions: Collection[CloudstackConnectivityActionModel],
        executor: ThreadPoolExecutor,
    ) -> None:
        existing_names = set()
        net_to_create = {}  # {(pg_name, host_name): action}

        for action in filter(is_set_action, actions):
            net_settings = self._get_network_settings(action)
            if net_settings.existed:
                existing_names.add(net_settings.name)
            else:
                vm = self.get_target(action)
                zone_id = vm.zone_id
                net_settings.zone_id = zone_id
                key = (net_settings.name, zone_id)
                net_to_create[key] = net_settings

        # check that existed networks exist
        self._networks.update(
            {n: self._api_service.Network.find_by_id_or_name(n) for n in existing_names}
        )

        # create networks
        tuple(executor.map(self._get_or_create_network, net_to_create.values()))

    def load_target(self, target_name: str) -> Any:
        return self._api_service.VM.get(target_name)

    def get_vnics(self, vm: CloudstackVirtualMachine) -> Collection[VnicInfo]:
        def get_vnic_info(vnic: Interface) -> VnicInfo:
            return VnicInfo(
                vnic.nic_id,
                vnic.interface_index,
                self._network_can_be_replaced(vnic.network_id),
            )

        return tuple(map(get_vnic_info, vm.get_interfaces()))

    def set_vlan(
        self,
        action: CloudstackConnectivityActionModel,
        target: CloudstackVirtualMachine | None = None,
    ) -> str:
        assert isinstance(target, CloudstackVirtualMachine)
        vnic_index = action.custom_action_attrs.vnic
        net_settings = self._get_network_settings(action)
        network = self._networks[net_settings.name]

        logger.info(f"Connecting {network} to the {target}.{vnic_index} iface")

        vnic = next(
            (
                x
                for x in target.get_interfaces()
                if str(x.interface_index) == vnic_index
            ),
            None,
        )
        if not vnic:
            vnic = target.attach_network(network.id_)
        elif vnic.network_id != network.id_:
            target.detach_network(vnic.network_id)
            vnic = target.attach_network(network.id_)

        return vnic.mac_address

    def remove_vlan(
        self,
        action: CloudstackConnectivityActionModel,
        target: CloudstackVirtualMachine | None = None,
    ) -> str:
        if not isinstance(target, CloudstackVirtualMachine):
            # skip disconnecting vNIC
            # CloudShell would call Connectivity one more time in teardown after VM was
            # deleted if disconnect for the first time failed
            logger.warning(VM_NOT_FOUND_MSG.format(action.custom_action_attrs.vm_uuid))
            return ""
        interface = target.get_interface_by_mac(action.connector_attrs.interface)
        if not interface:
            return ""
        logger.info(f"Disconnecting {interface.network} from the {target.vm_name}")
        target.detach_network(interface.network_id)
        return interface.mac_address

    def clear(self, action: CloudstackConnectivityActionModel, target: Any) -> str:
        """Executes before set VLAN actions or for rolling back failed.

        Returns updated interface if it's different from target name.
        """
        assert isinstance(target, CloudstackVirtualMachine)
        vnic_index = action.custom_action_attrs.vnic
        vnic = None
        if vnic_index:
            vnic = next(
                (
                    x
                    for x in target.get_interfaces()
                    if str(x.interface_index) == vnic_index
                ),
                None,
            )
        if not vnic:
            logger.info(f"VNIC {vnic_index} is not created. Skip disconnecting")
        else:
            logger.info(f"Disconnecting {vnic_index} vNIC from the {target.vm_name}")
            target.detach_network(vnic.network_id)
        return ""

    def post_connectivity(
        self,
        actions: Collection[CloudstackConnectivityActionModel],
        executor: ThreadPoolExecutor,
    ) -> None:
        def _cleanup(network_setting: NetworkSettings) -> None:
            if network_setting:
                network = self._api_service.Network.find_by_id_or_name(
                    network_setting.name, raise_error=False
                )
                if network:
                    network.remove()

        net_to_remove = {}  # {(pg_name, host_name): action}

        for action in actions:
            if self._is_remove_vlan_or_failed(action):
                net_settings = self._get_network_settings(action)
                if not net_settings.existed:
                    # we need to remove network only once for every used host
                    net_to_remove[net_settings.name] = net_settings

        # remove unused networks
        executor.map(_cleanup, net_to_remove.values())

    @staticmethod
    def _validate_network(
        network: Network,
        net_settings: NetworkSettings,
    ) -> None:
        pass

    def _get_or_create_network(self, net_settings: NetworkSettings) -> Network:
        with network_lock.lock(net_settings.name):
            try:
                # getting earlier created network
                network = self._api_service.Network.find_by_id_or_name(
                    net_settings.name
                )
            except NetworkNotFound:
                if net_settings.network_isolation == NetworkType.VLAN:
                    network_offering = self._api_service.NetworkOffering.get_by_type(
                        NetworkOfferingType.DEF_L2_VLAN
                    )
                else:
                    if net_settings.network_isolation == NetworkType.SHARED:
                        network_offering = (
                            self._api_service.NetworkOffering.get_by_type(
                                NetworkOfferingType.DEF_SHR
                            )
                        )
                    else:
                        network_offering = (
                            self._api_service.NetworkOffering.get_by_type(
                                NetworkOfferingType.DEF_ISO
                            )
                        )
                network = self._api_service.Network.create(
                    name=net_settings.name,
                    zone_id=net_settings.zone_id,
                    networking_offering=network_offering.id,
                    vlan_id=net_settings.vlan_id,
                    subnet_cidr_data=net_settings.subnet,
                )
            self._networks[net_settings.name] = network
        return network

    def _network_can_be_replaced(self, network_id: str) -> bool:
        net = self._api_service.Network.find_by_id(network_id)
        reserved_networks = self._resource_conf.reserved_networks
        not_quali_name = not net.name.startswith(f"{NETWORK_PREFIX}_VLAN_")
        if not net.name:
            result = True
        elif (
            net.name not in reserved_networks
            and not_quali_name
            and net.id_ != self._resource_conf.mgmt_network_id
        ):
            result = True
        else:
            result = False
        return result

    def _get_network_settings(
        self, action: CloudstackConnectivityActionModel
    ) -> NetworkSettings:
        return NetworkSettings.convert(action, self._resource_conf)

    def _is_remove_vlan_or_failed(
        self, action: CloudstackConnectivityActionModel
    ) -> bool:
        if is_remove_action(action):
            result = True
        else:
            results = self.results[action.action_id]
            success = results and all(result.success for result in results)
            result = not success
        return result
