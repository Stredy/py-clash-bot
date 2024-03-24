"""
A module for configuring Memu VMs.
"""

import time

import numpy
import psutil
from pymemuc import ConfigKeys

from pyclashbot.memu.pmc import pmc

cpu_count: int = psutil.cpu_count(logical=False)
total_mem = psutil.virtual_memory()[0] // 1024 // 1024

# see https://pymemuc.readthedocs.io/pymemuc.html#the-vm-configuration-keys-table
MEMU_CONFIGURATION: dict[ConfigKeys, str | int | float] = {
    "start_window_mode": 1,  # remember window position
    "win_scaling_percent2": 100,  # 100% scaling
    "is_customed_resolution": 1,
    "resolution_width": 419,
    "graphics_render_mode": "1",  # use DirectX to avoid black screenshot issue
    "resolution_height": 633,
    "vbox_dpi": 160,
    "cpucap": 50,
    "cpus": numpy.clip(cpu_count // 2, 2, 6),
    # "cpus": 1,
    "memory": numpy.clip(total_mem // 2, 2048, 4096),
    # "memory": 1024,
    "fps": 40,
    "turbo_mode": 0,
    "enable_audio": 0,
    "is_hide_toolbar": 1,
}


def set_vm_language(vm_index: int):
    """Set the language of the vm to english"""
    settings_uri = "--uri content://settings/system"
    set_language_commands = [
        f"shell content query {settings_uri} --where \"name='system_locales'\"",
        f"shell content delete {settings_uri} --where \"name='system_locales'\"",
        f"shell content insert {settings_uri} --bind name:s:system_locales --bind value:s:en-US",
        "shell setprop ctl.restart zygote",
    ]

    for command in set_language_commands:
        pmc.send_adb_command_vm(vm_index=vm_index, command=command)
        time.sleep(0.33)


def configure_vm(vm_index):
    """Configure the virtual machine with the given index."""
    for key, value in MEMU_CONFIGURATION.items():
        pmc.set_configuration_vm(key, str(value), vm_index=vm_index)

    set_vm_language(vm_index=vm_index)
    set_vm_language(vm_index=vm_index)
    set_vm_language(vm_index=vm_index)


if __name__ == "__main__":
    vm_index = 0
    print(f"Configuring VM {vm_index}...")
    configure_vm(vm_index)
    print(f"Configured VM {vm_index}")
