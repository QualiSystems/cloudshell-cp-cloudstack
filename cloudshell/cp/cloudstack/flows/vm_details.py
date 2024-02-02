from cloudshell.cp.core.flows import AbstractVMDetailsFlow
from cloudshell.cp.core.request_actions.models import VmDetailsData

from cloudshell.cp.cloudstack.actions.vm_details_actions import get_vm_details
from cloudshell.cp.cloudstack.models.deployed_app import VMFromTemplateDeployedApp
from cloudshell.cp.cloudstack.services.cloudstack_api_service import (
    CloudStackAPIService,
)


class CloudstackGetVMDetailsFlow(AbstractVMDetailsFlow):
    def __init__(self, resource_config, logger):
        """Init command.

        :param logging.Logger logger:
        """
        super().__init__(logger)
        self._resource_config = resource_config

    def _get_vm_details(self, deployed_app: VMFromTemplateDeployedApp) -> VmDetailsData:
        """Get VM Details.

        :param cloudshell.cp.core.request_actions.DeployedApp deployed_app:
        :rtype: cloudshell.cp.core.request_actions.models.VmDetailsData
        """
        network = deployed_app.mgmt_network_id or self._resource_config.mgmt_network_id
        api = CloudStackAPIService.from_config(self._resource_config, self._logger)
        vm = api.VM.get(deployed_app.vmdetails.uid)
        return get_vm_details(api, network, vm, self._logger)
