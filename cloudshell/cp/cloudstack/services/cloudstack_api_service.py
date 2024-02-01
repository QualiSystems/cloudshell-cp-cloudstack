from __future__ import annotations

from functools import cached_property
from logging import Logger

import attr

from cloudshell.cp.cloudstack.api_client.cloudstack_api import CloudStackAPIClient
from cloudshell.cp.cloudstack.entities.network import Network as _Network
from cloudshell.cp.cloudstack.entities.network_offering import (
    NetworkOffering as _NetworkOffering,
)
from cloudshell.cp.cloudstack.entities.vm import CloudstackVirtualMachine as _VM
from cloudshell.cp.cloudstack.models.resource_config import CloudstackResourceConfig


@attr.s(auto_attribs=True, str=False)
class CloudStackAPIService:
    _api_client: CloudStackAPIClient
    _logger: Logger

    @classmethod
    def connect(
        cls,
        cloudstack_host: str,
        api_key: str,
        secret_key: str,
        logger: Logger,
    ) -> CloudStackAPIService:
        logger.debug("Getting OpenStack Session")
        session = CloudStackAPIClient(cloudstack_host, api_key, secret_key)
        session.verify_connection(logger)
        return cls(session, logger)

    @classmethod
    def from_config(
        cls, conf: CloudstackResourceConfig, logger: Logger
    ) -> CloudStackAPIService:
        return cls.connect(conf.address, conf.api_key, conf.secret_key, logger)

    @cached_property
    def NetworkOffering(self) -> type[_NetworkOffering]:
        class NetworkOffering(_NetworkOffering):
            api = self._api_client
            _logger = self._logger

        return NetworkOffering

    @cached_property
    def Network(self) -> type[_Network]:
        class Network(_Network):
            api = self._api_client
            _logger = self._logger

        return Network

    @cached_property
    def VM(self) -> type[_VM]:
        class VM(_VM):
            _api = self._api_client
            _logger = self._logger

        return VM
