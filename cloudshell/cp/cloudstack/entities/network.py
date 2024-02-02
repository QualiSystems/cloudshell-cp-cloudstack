from __future__ import annotations

from logging import Logger
from typing import ClassVar

import attr

from cloudshell.cp.cloudstack.api_client.cloudstack_api import CloudStackAPIClient
from cloudshell.cp.cloudstack.entities.network_type import NetworkType
from cloudshell.cp.cloudstack.exceptions import (
    CreateNetworkError,
    NetworkInUse,
    NetworkNotFound,
)
from cloudshell.cp.cloudstack.models.connectivity_action_model import SubnetCidrData


@attr.s(auto_attribs=True, str=False)
class Network:
    api: ClassVar[CloudStackAPIClient]
    _logger: ClassVar[Logger]

    id_: str  # noqa: A003
    name: str
    network_type: NetworkType
    vlan_id: int | None
    is_external: bool

    def __str__(self) -> str:
        return f"Network '{self.name}'"

    @classmethod
    def from_dict(cls, net_dict: dict) -> Network:
        network_type = NetworkType(net_dict.get("type"))
        is_external = (
            network_type.value == NetworkType.SHARED
            or network_type.value == NetworkType.VLAN
        )
        return cls(
            net_dict["id"],
            net_dict["displaytext"],
            network_type=network_type,
            vlan_id=net_dict.get("vlan"),
            is_external=is_external,
        )

    @classmethod
    def find_by_vlan_id(cls, vlan_id: int) -> Network:
        networks = cls._list_networks({"vlan": vlan_id})
        try:
            network = networks[0]
        except (TypeError, IndexError):
            raise NetworkNotFound(vlan_id=vlan_id) from None
        return network

    @classmethod
    def find_by_id(cls, id_: str) -> Network:
        networks = cls._list_networks({"id": id_})
        try:
            network = networks[0]
        except (TypeError, IndexError):
            raise NetworkNotFound(id_=id_) from None
        return network

    @classmethod
    def find_by_name(cls, name: str, raise_error=True) -> Network:
        networks = cls._list_networks({"name": name})
        if networks is None:
            raise NetworkNotFound(name=name)
        for network in networks:
            if network.name == name:
                return network
        if raise_error:
            raise NetworkNotFound(name=name)

    @classmethod
    def find_by_id_or_name(cls, data: str, raise_error=True) -> Network:
        networks = cls._list_networks()
        if networks is None:
            raise NetworkNotFound(name=data)
        for network in networks:
            if network.name == data or network.id_ == data:
                return network
        if raise_error:
            raise NetworkNotFound(name=data)

    @classmethod  # noqa: A003
    def all(cls) -> list[Network]:  # noqa: A003
        cls._logger.debug("Get all networks")
        return cls._list_networks()

    @classmethod
    def _list_networks(cls, network_filter: dict | None = None) -> list[Network]:
        inputs = {"command": "listNetworks"}
        if network_filter:
            inputs.update(network_filter)
        # add network_filter by tags
        response = cls.api.send_request(inputs)
        networks = response.json()["listnetworksresponse"]["network"]

        if response.status_code != 200 and response.status_code != 201:
            raise Exception(
                f"Unable to verify API response. " f"{response.status_code}."
            )
        # for net_dict in offerings:
        return [cls.from_dict(net_dict) for net_dict in networks]

    @classmethod
    def create(
        cls,
        name: str,
        zone_id: str,
        networking_offering: str,
        *,
        vlan_id: str | None = None,
        subnet_cidr_data: SubnetCidrData | None = None,
        qnq: bool = False,
        physical_iface_name: str | None = None,
    ) -> Network:
        inputs = {
            "command": "createNetwork",
            "name": name,
            "zoneid": zone_id,
            "networkofferingid": networking_offering,
            "vlan": vlan_id,
            "bypassvlanoverlapcheck": "True",
        }
        if subnet_cidr_data:
            inputs.update(
                {
                    "gateway": str(subnet_cidr_data.gateway),
                    "netmask": str(subnet_cidr_data.cidr.netmask),
                    "startip": str(subnet_cidr_data.allocation_pool[0]),  # type: ignore
                    "endip": str(subnet_cidr_data.allocation_pool[1]),  # type: ignore
                }
            )
        cls._logger.debug(f"Creating a network {name}")
        response = cls.api.send_request(inputs)
        if response.status_code != 200 and response.status_code != 201:
            raise CreateNetworkError(
                name=name,
                vlan_id=vlan_id,
                error_message=response.json()
                .get("createnetworkresponse", {})
                .get("errortext"),
            )
        response_json = response.json()
        id_ = (
            response_json.get("createnetworkresponse", {}).get("network", {}).get("id")
        )
        job_id = response_json.get("createnetworkresponse", {}).get("jobid")
        status = cls.api.wait_for_job(job_id)
        if status != 1:
            raise CreateNetworkError(
                name=name,
                vlan_id=vlan_id,
                error_message=f"Network creation process complete with "
                f"status: {status}",
            )
        return cls.find_by_id(id_)

    def remove(self, raise_in_use: bool = True) -> None:
        self._logger.debug(f"Removing {self}")
        inputs = {"command": "deleteNetwork", "id": self.id_, "forced": "True"}
        response = self.api.send_request(inputs)
        if raise_in_use and (
            response.status_code != 200 and response.status_code != 201
        ):
            raise NetworkInUse(self)
        job_id = response.json().get("deletenetworkresponse", {}).get("jobid")
        status = self.api.wait_for_job(job_id)
        if status != 1:
            self._logger.warning(
                f"Network deletion process failed with status: {status}"
            )
