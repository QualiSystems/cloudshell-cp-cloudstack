from __future__ import annotations

from collections.abc import Generator
from enum import Enum
from logging import Logger
from typing import ClassVar

import attr

from cloudshell.cp.cloudstack.api_client.cloudstack_api import CloudStackAPIClient


class NetworkOfferingType(Enum):
    DEF_SHR_SG = "DefaultSharedNetworkOfferingWithSGService"
    DEF_SHR = "DefaultSharedNetworkOffering"
    DEF_TUN_SHR_SG = "DefaultTungstenSharedNetworkOfferingWithSGService"
    DEF_ISO_SRC_NAT = "DefaultIsolatedNetworkOfferingWithSourceNatService"
    DEF_ISO = "DefaultIsolatedNetworkOffering"
    DEF_SHR_NETSC_ELB = "DefaultSharedNetscalerEIPandELBNetworkOffering"
    DEF_ISO_VPC = "DefaultIsolatedNetworkOfferingForVpcNetworks"
    DEF_ISO_NET_VPC = "DefaultIsolatedNetworkOfferingForVpcNetworksNoLB"
    DEF_ISO_NET_VPC_LB = "DefaultIsolatedNetworkOfferingForVpcNetworksWithInternalLB"
    DEF_L2 = "DefaultL2NetworkOffering"
    DEF_L2_VLAN = "DefaultL2NetworkOfferingVlan"
    DEF_L2_CFGDRV = "DefaultL2NetworkOfferingConfigDrive"
    DEF_L2_VLAN_CFGDRV = "DefaultL2NetworkOfferingConfigDriveVlan"
    QCK_CLD = "QuickCloudNoServices"
    DEF_KUBE = "DefaultNetworkOfferingforKubernetesService"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(value.lower())


@attr.s(auto_attribs=True, str=False)
class NetworkOffering:
    api: ClassVar[CloudStackAPIClient]
    _logger: ClassVar[Logger]

    id: str  # noqa: A003
    type: str
    network_type: NetworkOfferingType
    state: int | None
    specify_vlan: bool

    def __str__(self) -> str:
        return f"Network Offering '{self.type}'"

    @classmethod
    def from_dict(cls, net_dict: dict) -> NetworkOffering:
        return cls(
            net_dict["id"],
            net_dict["traffictype"],
            network_type=NetworkOfferingType(net_dict["name"]),
            state=net_dict["state"],
            specify_vlan=net_dict["specifyvlan"],
        )

    @classmethod
    def get_by_id(cls, id_: str) -> NetworkOffering:
        cls._logger.debug(f"Getting a network with ID '{id_}'")
        for net_offering in cls.all():
            if net_offering.id == id_:
                return net_offering

    @classmethod
    def get_by_type(cls, type: NetworkOfferingType) -> NetworkOffering:
        cls._logger.debug(f"Getting a network with ID '{type}'")
        for net_offering in cls.all():
            if net_offering.network_type == type:
                return net_offering

    # @classmethod
    # def find_first(cls, name: str) -> NetworkOffering:
    #     cls._logger.debug(f"Searching for first network with name '{name}'")
    #     offerings = cls.all()
    #     for net_offering in offerings:
    #         if net_offering.network_type["name"] == name:
    #             break
    #     else:
    #         raise NetworkNotFound(name=name)
    #     return cls.from_dict(net_dict)

    @classmethod  # noqa: A003
    def all(cls) -> Generator[NetworkOffering, None, None]:  # noqa: A003
        cls._logger.debug("Get all network offerings")
        inputs = {"command": "listNetworkOfferings"}

        response = cls.api.send_request(inputs)
        offerings = response.json()["listnetworkofferingsresponse"]["networkoffering"]

        if response.status_code != 200 and response.status_code != 201:
            raise Exception(
                f"Unable to verify API response. " f"{response.status_code}."
            )
        for net_dict in offerings:
            yield cls.from_dict(net_dict)
