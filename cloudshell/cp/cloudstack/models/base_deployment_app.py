from __future__ import annotations

import re
from typing import Any

from attrs import define, field


class CloudstackDeploymentAppAttributeNames:
    service_offering_id = "Service Offering Id"
    template_id = "Template Id"
    zone_id = "Zone Id"
    pod_id = "Pod Id"
    group = "Group"
    hostname = "Hostname"
    auto_power_on = "Auto Power On"
    auto_power_off = "Auto Power Off"
    wait_for_ip = "Wait for IP"
    auto_delete = "Auto Delete"
    autoload = "Autoload"
    ip_regex = "IP Regex"
    refresh_ip_timeout = "Refresh IP Timeout"
    cluster_id = "Cluster Id"
    disk_offering_id = "Disk Offering Id"
    autogenerated_name = "Autogenerated Name"
    mgmt_network_id = "Mgmt Network Id"

    private_ip = "Private IP"
    cpu_num = "CPU"
    ram_amount = "RAM"
    hdd_specs = "HDD"
    copy_source_uuid = "Copy source UUID"


@define
class ResourceAttrRODeploymentPath:
    name: str
    default: Any = None

    def get_key(self, instance) -> str:
        dp = instance.DEPLOYMENT_PATH
        return f"{dp}.{self.name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.attributes.get(self.get_key(instance), self.default)


class ResourceBoolAttrRODeploymentPath(ResourceAttrRODeploymentPath):
    TRUE_VALUES = {"true", "yes", "y"}
    FALSE_VALUES = {"false", "no", "n"}

    def __get__(self, instance, owner):
        val = super().__get__(instance, owner)
        if val is self or val is self.default or not isinstance(val, str):
            return val
        if val.lower() in self.TRUE_VALUES:
            return True
        if val.lower() in self.FALSE_VALUES:
            return False
        raise ValueError(f"{self.name} is boolean attr, but value is {val}")


class ResourceListAttrRODeploymentPath(ResourceAttrRODeploymentPath):
    def __init__(self, name, sep=";", default=None):
        if default is None:
            default = []
        super().__init__(name, default)
        self._sep = sep

    def __get__(self, instance, owner) -> list[str]:
        val = super().__get__(instance, owner)
        if val is self or val is self.default or not isinstance(val, str):
            return val
        return list(filter(bool, map(str.strip, val.split(self._sep))))


class IncorrectHddSpecFormat(Exception):
    def __init__(self, text: str):
        self.text = text
        super().__init__(
            f"'{text}' is not a valid HDD format. Should be "
            f"Hard Disk Label: Disk Size (GB)"
        )


class ResourceIntAttrRODeploymentPath(ResourceAttrRODeploymentPath):
    def __get__(self, instance, owner) -> int | None:
        val = super().__get__(instance, owner)
        if val is self or val is self.default:
            return val
        return int(val) if val else None


class ResourceFloatAttrRODeploymentPath(ResourceAttrRODeploymentPath):
    def __get__(self, instance, owner) -> float | None:
        val = super().__get__(instance, owner)
        if val is self or val is self.default:
            return val
        return float(val) if val else None


class HddSpecsAttrRO(ResourceListAttrRODeploymentPath):
    def __get__(self, instance, owner) -> list[HddSpec]:
        val = super().__get__(instance, owner)
        if isinstance(val, list):
            val = list(map(HddSpec.from_str, val))
        return val


@define
class HddSpec:
    num: int
    size: float = field(order=False)

    @classmethod
    def from_str(cls, text: str) -> HddSpec:
        try:
            num, size = text.split(":")
            num = int(re.search(r"\d+", num).group())  # type: ignore
            size = float(size)  # type: ignore
        except ValueError:
            raise IncorrectHddSpecFormat(text)
        return cls(num, size)  # type: ignore

    @property
    def size_in_kb(self) -> int:
        return int(self.size * 2**20)
