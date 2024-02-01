from cloudshell.cp.cloudstack.services.cloudstack_api_service import (
    CloudStackAPIService,
)


class VMState:
    def __init__(self, cloudstack_service: CloudStackAPIService, vm_uuid: str):
        self.vm = cloudstack_service.VM.get(vm_uuid)

    def power_on_vm(self):
        self.vm.power_on_vm()

    def power_off_vm(self):
        self.vm.power_off_vm()

    def reconfigure_vm(self):
        self.vm.reconfigure_vm()
