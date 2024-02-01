from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cloudshell.cp.cloudstack.entities import port, vm, vm_network


class CloudstackBaseException(Exception):
    """Base OpenStack exception."""


class CloudstackNetworkException(CloudstackBaseException):
    """Network exception."""


class FreeSubnetIsNotFound(CloudstackNetworkException):
    def __init__(self):
        super().__init__("All Subnets Exhausted")


class InstanceNotFound(CloudstackBaseException):
    def __init__(self, *, id_: str | None = None, name: str | None = None):
        assert id_ or name
        if id_:
            msg = f"Instance with id '{id_}' not found"
        else:
            msg = f"Instance with name '{name}' not found"

        super().__init__(msg)


class CreateNetworkError(CloudstackNetworkException):
    def __init__(
        self,
        *,
        name: str | None = None,
        vlan_id: str | None = None,
        error_message: str | None = None,
    ):
        assert vlan_id or name
        if vlan_id:
            msg = (
                f"Failed to create "
                f"Network with vlan id '{vlan_id}' with {error_message}"
            )
        else:
            msg = (
                f"Failed to create " f"Network with name '{name}' with {error_message}"
            )

        super().__init__(msg)


class InstanceErrorState(CloudstackBaseException):
    def __init__(self, instance: vm.CloudstackVirtualMachine, msg: str):
        super().__init__(
            f"The {instance.vm_data['displayname']} status is error. " f"Message: {msg}"
        )


class MgmtIfaceIsMissed(CloudstackBaseException):
    def __init__(self, instance: vm.CloudstackVirtualMachine):
        super().__init__(f"Cannot find management interface on the {instance}")


class ImageNotFound(CloudstackBaseException):
    def __init__(self, id_):
        super().__init__(f"Image with id '{id_}' not found")


class FlavorNotFound(CloudstackBaseException):
    def __init__(self, *, id_: str | None = None, name: str | None = None):
        assert id_ or name
        if id_:
            msg = f"Flavor with id '{id_}' not found"
        else:
            msg = f"Flavor with name '{name}' not found"

        super().__init__(msg)


class PortNotFound(CloudstackNetworkException):
    def __init__(self, *, id_: str | None = None, name: str | None = None):
        assert id_ or name
        if id_:
            msg = f"Port with id '{id_}' not found"
        else:
            msg = f"Port with name '{name}' not found"

        super().__init__(msg)


class PortIsNotGone(CloudstackNetworkException):
    def __init__(self, port: port.Port):
        super().__init__(f"The {port} is not gone")


class PortIsNotAttached(CloudstackNetworkException):
    def __init__(self, network_name: str, instance: vm.CloudstackVirtualMachine):
        super().__init__(
            f"Failed to attach {instance.vm_name} instance to "
            f"{network_name} network"
        )


class TrunkNotFound(CloudstackNetworkException):
    def __init__(self, *, id_: str | None = None, name: str | None = None):
        assert id_ or name
        if id_:
            msg = f"Trunk with id '{id_}' not found"
        else:
            msg = f"Trunk with name '{name}' not found"

        super().__init__(msg)


class NetworkNotFound(CloudstackNetworkException):
    def __init__(
        self,
        *,
        id_: str | None = None,
        name: str | None = None,
        vlan_id: int | None = None,
    ):
        assert id_ or name or vlan_id
        if id_:
            msg = f"Network with id '{id_}' not found"
        elif name:
            msg = f"Network with name '{name}' not found"
        else:
            msg = f"Network with VLAN ID {vlan_id} not found"

        super().__init__(msg)


class NetworkInUse(CloudstackNetworkException):
    def __init__(self, network: vm_network.Network):
        super().__init__(f"{network} in use")


class NetworkWithVlanIsNotCreatedByCloudShell(CloudstackNetworkException):
    def __init__(self, network: vm_network.Network, vlan_id: int):
        super().__init__(f"{network} with VLAN {vlan_id} is not created by CloudShell")


class SubnetNotFound(CloudstackNetworkException):
    def __init__(self, *, id_: str | None = None, name: str | None = None):
        assert id_ or name
        if id_:
            msg = f"Subnet with id '{id_}' not found"
        else:
            msg = f"Subnet with name '{name}' not found"

        super().__init__(msg)


class FloatingIpNotFound(CloudstackNetworkException):
    def __init__(self, *, id_: str | None = None, ip: str | None = None):
        assert id_ or ip
        if id_:
            msg = f"Floating IP with id '{id_}' not found"
        else:
            msg = f"Floating IP '{ip}' not found"
        super().__init__(msg)


class SecurityGroupNotFound(CloudstackNetworkException):
    def __init__(self, *, id_: str | None = None):
        super().__init__(f"Security Group with id '{id_}' not found")


class NotSupportedConsoleType(CloudstackBaseException):
    """Console type is not supported."""

    def __init__(self, console_type: str, supported_types: Iterable[str]):
        self._console_type = console_type
        self._supported_types = supported_types

    def __str__(self):
        return (
            f"{self._console_type} is not supported. "
            f"You have to use {list(self._supported_types)}"
        )


class SubnetCidrFormatError(CloudstackBaseException):
    def __init__(self):
        super().__init__(
            "Subnet CIDR format is wrong. Format - CIDR[;Gateway][;First_IP-Last_IP]. "
            "For example, `192.168.10.0/24;192.168.10.1;192.168.10.30-192.168.10.50`"
        )


class PrivateIpIsNotInMgmtNetwork(CloudstackBaseException):
    def __init__(self, ip: str, network: vm_network.Network):
        super().__init__(f"Private IP {ip} is not inside the {network}")
