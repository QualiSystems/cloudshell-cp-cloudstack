from logging import Logger

from cloudshell.cp.core.request_actions.models import (
    DeployedApp,
    VmDetailsData,
    VmDetailsNetworkInterface,
    VmDetailsProperty,
)

from cloudshell.cp.cloudstack.entities.vm import CloudstackVirtualMachine
from cloudshell.cp.cloudstack.models.resource_config import CloudstackResourceConfig
from cloudshell.cp.cloudstack.services.cloudstack_api_service import (
    CloudStackAPIService,
)


def get_vm(
    resource_conf: CloudstackResourceConfig, deployed_app: DeployedApp, logger: Logger
):
    cloudstack_api = resource_conf.get_cloudstack_api()
    return CloudstackVirtualMachine(cloudstack_api, deployed_app.vmdetails.uid, logger)


def _sort_networks_key(mgmt_net_id: str):
    def sort(net_iface: VmDetailsNetworkInterface) -> bool:
        # iface with mgmt network would be first
        return net_iface.networkId != mgmt_net_id

    return sort


def get_vm_details(
    cloudstack_api: CloudStackAPIService,
    mgmt_network_id: str,
    vm: CloudstackVirtualMachine,
    logger,
):
    logger.info(
        f"Getting Cloudstack VirtualMachine details for "
        f"CloudstackVirtualMachine: {vm.vm_name}"
    )

    vm_instance_data = [
        # VmDetailsProperty(key='Instance Name', value=vm.vm_data['name'])
        VmDetailsProperty(key="CPU", value=f"{vm.num_cpu} vCPU"),
        VmDetailsProperty(key="Memory", value=vm.memory_size),
        VmDetailsProperty(key="Guest OS", value=vm.guest_os),
        VmDetailsProperty(key="ID", value=vm.vm_uuid),
    ]

    vm_network_data = []

    for nic in vm.get_interfaces():
        primary = False
        if nic.network_id == mgmt_network_id:
            primary = True
        network_data = [
            VmDetailsProperty(key="MAC Address", value=nic.mac_address),
            VmDetailsProperty(key="IP", value=nic.ip_address),
        ]
        vlan_id = cloudstack_api.Network.find_by_id(nic.network_id).vlan_id

        current_interface = VmDetailsNetworkInterface(
            interfaceId=nic.mac_address,
            networkId=vlan_id,
            isPrimary=primary,
            isPredefined=primary,
            networkData=network_data,
            privateIpAddress=nic.ip_address,
            publicIpAddress=nic.public_ip_address,
        )
        vm_network_data.append(current_interface)
    return VmDetailsData(
        vmInstanceData=vm_instance_data,
        vmNetworkData=sorted(vm_network_data, key=_sort_networks_key(mgmt_network_id)),
        appName=vm.vm_name,
    )
