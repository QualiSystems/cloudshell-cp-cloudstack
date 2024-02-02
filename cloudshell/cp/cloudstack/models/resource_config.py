from __future__ import annotations

from attrs import define

from cloudshell.shell.standards.core.resource_conf import BaseConfig, attr

STATIC_SHELL_NAME = "Generic Static Cloudstack VM 2G"


class CloudstackAttributeNames:
    api_key = "API Key"
    secret_key = "Secret Key"
    enable_tags = "Enable Tags"
    mgmt_network_id = "Mgmt Network Id"
    reserved_networks = "Reserved Networks"


@define(slots=False, str=False)
class CloudstackResourceConfig(BaseConfig):
    ATTR_NAMES = CloudstackAttributeNames

    api_key: str = attr(ATTR_NAMES.api_key, is_password=True)
    secret_key: str = attr(ATTR_NAMES.secret_key, is_password=True)
    enable_tags: bool = attr(ATTR_NAMES.enable_tags)
    mgmt_network_id: str = attr(ATTR_NAMES.mgmt_network_id)
    reserved_networks: list[str] = attr(ATTR_NAMES.reserved_networks)

    @property
    def is_static(self) -> bool:
        return STATIC_SHELL_NAME == self.shell_name
