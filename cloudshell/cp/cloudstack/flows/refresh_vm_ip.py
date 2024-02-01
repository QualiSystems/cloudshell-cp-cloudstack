from __future__ import annotations

from contextlib import suppress
from logging import Logger

from cloudshell.cp.cloudstack.flows.vm_details import get_vm
from cloudshell.cp.cloudstack.models.deployed_app import VMFromTemplateDeployedApp
from cloudshell.cp.cloudstack.models.resource_config import CloudstackResourceConfig
from cloudshell.cp.cloudstack.services.cloudstack_api_service import (
    CloudStackAPIService,
)


def refresh_ip(
    deployed_app: VMFromTemplateDeployedApp,
    resource_conf: CloudstackResourceConfig,
    logger: Logger,
) -> str | None:
    logger.info("Starting collecting vm detail command...")
    with suppress(Exception):
        api = CloudStackAPIService.from_config(resource_conf, logger)
        vm_handler = api.VM.get(deployed_app.vmdetails.uid)
        interface = vm_handler.get_vm_ip(deployed_app.ip_regex)

        logger.info("Finished collecting vm detail command")
        if interface:
            if interface.ip_address:
                deployed_app.update_private_ip(deployed_app.name, interface.ip_address)
            if interface.public_ip_address:
                deployed_app.update_public_ip(interface.public_ip_address)
            return interface.ip_address
