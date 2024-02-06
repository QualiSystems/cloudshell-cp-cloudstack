from unittest.mock import MagicMock, patch

import pytest

from cloudshell.cp.core.cancellation_manager import CancellationContextManager
from cloudshell.cp.core.reservation_info import ReservationInfo
from cloudshell.shell.core.driver_context import (
    AppContext,
    ConnectivityContext,
    ReservationContextDetails,
    ResourceCommandContext,
    ResourceContextDetails,
)

from cloudshell.cp.cloudstack.constants import SHELL_NAME
from cloudshell.cp.cloudstack.models.resource_config import CloudstackResourceConfig


@pytest.fixture()
def logger():
    return MagicMock()


@pytest.fixture
def sleepless(monkeypatch):
    with patch("time.sleep"):
        yield


@pytest.fixture()
def connectivity_context() -> ConnectivityContext:
    return ConnectivityContext(
        server_address="localhost",
        cloudshell_api_port="5000",
        quali_api_port="5001",
        admin_auth_token="token",
        cloudshell_version="2021.2",
        cloudshell_api_scheme="https",
    )


@pytest.fixture()
def resource_context_details() -> ResourceContextDetails:
    return ResourceContextDetails(
        id="id",
        name="name",
        fullname="fullname",
        type="type",
        address="192.168.1.2",
        model=SHELL_NAME,
        family="family",
        description="",
        attributes={},
        app_context=AppContext("", ""),
        networks_info=None,
        shell_standard="",
        shell_standard_version="",
    )


@pytest.fixture()
def reservation_context_details() -> ReservationContextDetails:
    return ReservationContextDetails(
        environment_name="env name",
        environment_path="env path",
        domain="domain",
        description="",
        owner_user="user",
        owner_email="email",
        reservation_id="rid",
        saved_sandbox_name="name",
        saved_sandbox_id="id",
        running_user="user",
        cloud_info_access_key="",
    )


@pytest.fixture
def reservation_info(reservation_context_details):
    return ReservationInfo._from_reservation_context(reservation_context_details)


@pytest.fixture()
def resource_command_context(
    connectivity_context, resource_context_details, reservation_context_details
) -> ResourceCommandContext:
    return ResourceCommandContext(
        connectivity_context, resource_context_details, reservation_context_details, []
    )


@pytest.fixture()
def cs_api():
    return MagicMock(DecryptPassword=lambda pswd: MagicMock(Value=pswd))


@pytest.fixture()
def cancellation_manager() -> CancellationContextManager:
    return CancellationContextManager(MagicMock(is_cancelled=False))


@pytest.fixture()
def resource_conf(resource_command_context, cs_api) -> CloudstackResourceConfig:
    api_key = "API_KEY"
    secret_key = "SECRET_KEY"
    mgmt_network_id = "network-id-here"
    reserved_networks = "id1;id2"
    enable_tags = "false"

    a_name = CloudstackResourceConfig.ATTR_NAMES
    get_full_a_name = lambda n: f"{SHELL_NAME}.{n}"  # noqa: E731
    resource_command_context.resource.attributes.update(
        {
            get_full_a_name(a_name.api_key): api_key,
            get_full_a_name(a_name.secret_key): secret_key,
            get_full_a_name(a_name.mgmt_network_id): mgmt_network_id,
            get_full_a_name(a_name.reserved_networks): reserved_networks,
            get_full_a_name(a_name.enable_tags): enable_tags,
        }
    )

    class Cfg(CloudstackResourceConfig):
        __dict__ = {}

        def __setattr__(self, key, value):
            object.__setattr__(self, key, value)

    conf = Cfg.from_context(resource_command_context, cs_api)

    return conf
