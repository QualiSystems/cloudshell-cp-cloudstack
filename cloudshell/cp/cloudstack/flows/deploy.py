import time
from logging import Logger

from cloudshell.cp.core.request_actions.models import DeployAppResult

from cloudshell.cp.cloudstack.actions.vm_details import get_vm_details
from cloudshell.cp.cloudstack.models.deploy_app import VMFromTemplateDeployApp
from cloudshell.cp.cloudstack.models.resource_config import CloudstackResourceConfig
from cloudshell.cp.cloudstack.services.cloudstack_api_service import (
    CloudStackAPIService,
)


class DeployFlow:
    def __init__(self, resource_config: CloudstackResourceConfig, logger: Logger):
        self.resource_config = resource_config
        self.cloudstack_service = CloudStackAPIService.from_config(
            resource_config, logger
        )
        self._logger = logger

    def deploy_from_template(self, deploy_action: VMFromTemplateDeployApp):

        network_id = (
            deploy_action.mgmt_network_id or self.resource_config.mgmt_network_id
        )

        vm = self.cloudstack_service.VM.create(deploy_action, self.resource_config)

        vm.wait_for_vm_to_start()
        vm_details_data = get_vm_details(
            self.cloudstack_service, network_id, vm, self._logger
        )

        if vm_details_data is None:
            return DeployAppResult(
                actionId=deploy_action.actionId,
                success=False,
                errorMessage=f"Unable to extract CloudstackVirtualMachine details. "
                f"CloudstackVirtualMachine Name: {vm.vm_name}",
            )

        return DeployAppResult(
            actionId=deploy_action.actionId,
            success=True,
            vmUuid=vm.vm_uuid,
            vmName=vm.vm_name,
            deployedAppAddress=vm.vm_data.get("nic", [{}])[0].get("ipaddress"),
            vmDetailsData=vm_details_data,
        )
