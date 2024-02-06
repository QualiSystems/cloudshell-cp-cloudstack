from unittest.mock import Mock

from cloudshell.cp.cloudstack.constants import SHELL_NAME
from cloudshell.cp.cloudstack.models.resource_config import CloudstackResourceConfig

RESOURCE_NAME = "cloudstack"
RESOURCE_FAMILY = "CS_CloudProvider"
RESOURCE_ADDRESS = "localhost"
MGMT_NETWORK_ID = "network-id-here"
API_KEY = "API_KEY"
SECRET_KEY = "SECRET_KEY"

RESERVED_NETWORKS = "id1;id2"
EXPECTED_RESERVED_NETWORKS = ["id1", "id2"]
ENABLE_TAGS = "true"
EXPECTED_ENABLE_TAGS = True


def test_resource_config(resource_command_context, cs_api):
    a_name = CloudstackResourceConfig.ATTR_NAMES
    get_full_a_name = lambda n: f"{SHELL_NAME}.{n}"  # noqa: E731
    resource_command_context.resource.name = RESOURCE_NAME
    resource_command_context.resource.family = RESOURCE_FAMILY
    resource_command_context.resource.address = RESOURCE_ADDRESS
    resource_command_context.resource.attributes.update(
        {
            get_full_a_name(a_name.api_key): API_KEY,
            get_full_a_name(a_name.secret_key): SECRET_KEY,
            get_full_a_name(a_name.mgmt_network_id): MGMT_NETWORK_ID,
            get_full_a_name(a_name.reserved_networks): RESERVED_NETWORKS,
            get_full_a_name(a_name.enable_tags): ENABLE_TAGS,
        }
    )
    conf = CloudstackResourceConfig.from_context(resource_command_context, cs_api)

    assert conf.name == RESOURCE_NAME
    assert conf.family_name == RESOURCE_FAMILY
    assert conf.address == RESOURCE_ADDRESS
    assert conf.api_key == API_KEY
    assert conf.secret_key == SECRET_KEY
    assert conf.mgmt_network_id == MGMT_NETWORK_ID
    assert conf.reserved_networks == EXPECTED_RESERVED_NETWORKS
    assert conf.enable_tags == EXPECTED_ENABLE_TAGS


def test_from_cs_resource_details(cs_api):
    a_name = CloudstackResourceConfig.ATTR_NAMES
    get_full_a_name = lambda n: f"{SHELL_NAME}.{n}"  # noqa: E731
    r_attrs = {
        get_full_a_name(a_name.api_key): API_KEY,
        get_full_a_name(a_name.secret_key): SECRET_KEY,
        get_full_a_name(a_name.mgmt_network_id): MGMT_NETWORK_ID,
        get_full_a_name(a_name.reserved_networks): RESERVED_NETWORKS,
        get_full_a_name(a_name.enable_tags): ENABLE_TAGS,
    }
    r_attrs = [Mock(Name=k, Value=v) for k, v in r_attrs.items()]

    details = Mock(
        Name=RESOURCE_NAME,
        ResourceModelName=SHELL_NAME,
        ResourceFamilyName=RESOURCE_FAMILY,
        Address=RESOURCE_ADDRESS,
        ResourceAttributes=r_attrs,
    )

    conf = CloudstackResourceConfig.from_cs_resource_details(details, cs_api)

    assert conf.name == RESOURCE_NAME
    assert conf.family_name == RESOURCE_FAMILY
    assert conf.address == RESOURCE_ADDRESS
    assert conf.api_key == API_KEY
    assert conf.secret_key == SECRET_KEY
    assert conf.mgmt_network_id == MGMT_NETWORK_ID
    assert conf.reserved_networks == EXPECTED_RESERVED_NETWORKS
    assert conf.enable_tags == EXPECTED_ENABLE_TAGS
