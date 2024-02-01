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


# @classmethod
# def from_cs_resource_details(
#     cls,
#     details: ResourceInfo,
#     api: CloudShellAPISession,
# ) -> CloudstackResourceConfig:
#     attrs = ResourceInfoAttrGetter(
#         cls, password_decryptor(api), details
#     ).get_attrs()
#     converter = cls._CONVERTER(cls, attrs)
#     return cls(
#         name=details.Name,
#         shell_name=details.ResourceModelName,
#         family_name=details.ResourceFamilyName,
#         address=details.Address,
#         api=api,
#         **converter.convert(),
#     )


# class ResourceInfoAttrGetter(AbsAttrsGetter):
#     def __init__(
#         self,
#         model_cls: type[MODEL],
#         decrypt_password: Callable[[str], str],
#         details: ResourceInfo,
#     ):
#         super().__init__(model_cls, decrypt_password)
#         self.details = details
#         self._attrs = {a.Name: a.Value for a in details.ResourceAttributes}
#         self.shell_name = details.ResourceModelName
#         self.family_name = details.ResourceFamilyName
#
#     def _extract_attr_val(self, f: Attribute, meta: AttrMeta) -> str:
#         key = self._get_key(meta)
#         return self._attrs[key]
#
#     def _get_key(self, meta: AttrMeta) -> str:
#         namespace = self._get_namespace(meta.namespace_type)
#         return f"{namespace}.{meta.name}"
#
#     def _get_namespace(self, namespace_type: NameSpaceType) -> str:
#         if namespace_type is NameSpaceType.SHELL_NAME:
#             namespace = self.shell_name
#         elif namespace_type is NameSpaceType.FAMILY_NAME:
#             namespace = self.family_name
#         else:
#             raise ValueError(f"Unknown namespace: {namespace_type}")
#         return namespace
