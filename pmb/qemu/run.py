"""
Copyright 2017 Pablo Castellano

This file is part of pmbootstrap.

pmbootstrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pmbootstrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pmbootstrap.  If not, see <http://www.gnu.org/licenses/>.
"""
import logging
import os
import shutil

import pmb.build
import pmb.chroot
import pmb.chroot.apk
import pmb.chroot.other
import pmb.chroot.initfs
import pmb.helpers.devices
import pmb.helpers.run
import pmb.parse.arch


def system_image(args, device):
    """
    Returns path to system image for specified device. In case that it doesn't
    exist, raise and exception explaining how to generate it.
    """
    path = args.work + "/chroot_native/home/user/rootfs/" + device + ".img"
    if not os.path.exists(path):
        logging.debug("Could not find system image: " + path)
        img_command = "pmbootstrap install"
        if device != args.device:
            img_command = ("pmbootstrap config device " + device +
                           "' and '" + img_command)
        message = "The system image '{0}' has not been generated yet, please" \
                  " run '{1}' first.".format(device, img_command)
        raise RuntimeError(message)
    return path


def which_qemu(args, arch):
    """
    Finds the qemu executable or raises an exception otherwise
    """
    executable = "qemu-system-" + arch
    if shutil.which(executable):
        return executable
    else:
        raise RuntimeError("Could not find the '" + executable + "' executable"
                           " in your PATH. Please install it in order to"
                           " run qemu.")


def which_spice(args):
    """
    Finds some SPICE executable or raises an exception otherwise
    :returns: tuple (spice_was_found, path_to_spice_executable)
    """
    executables = ["remote-viewer", "spicy"]
    for executable in executables:
        if shutil.which(executable):
            return True, executable
    return False, ""


def spice_command(args):
    """
    Generate the full SPICE command with arguments connect to
    the virtual machine
    :returns: tuple (dict, list), configuration parameters and spice command
    """
    parameters = {
        "spice_addr": "127.0.0.1",
        "spice_port": "8077"
    }
    if args.no_spice:
        parameters["enable_spice"] = False
        return parameters, []
    found_spice, spice_bin = which_spice(args)
    if not found_spice:
        parameters["enable_spice"] = False
        return parameters, []
    spice_addr = parameters["spice_addr"]
    spice_port = parameters["spice_port"]
    commands = {
        "spicy": ["spicy", "-h", spice_addr, "-p", spice_port],
        "remote-viewer": [
            "remote-viewer",
            "spice://" + spice_addr + "?port=" + spice_port
        ]
    }
    parameters["enable_spice"] = True
    return parameters, commands[spice_bin]


def qemu_command(args, arch, device, img_path, config):
    """
    Generate the full qemu command with arguments to run postmarketOS
    """
    qemu_bin = which_qemu(args, arch)
    deviceinfo = pmb.parse.deviceinfo(args, device=device)
    cmdline = deviceinfo["kernel_cmdline"]
    if args.cmdline:
        cmdline = args.cmdline
    logging.info("cmdline: " + cmdline)

    rootfs = args.work + "/chroot_rootfs_" + device
    command = [qemu_bin]
    command += ["-kernel", rootfs + "/boot/vmlinuz-postmarketos"]
    command += ["-initrd", rootfs + "/boot/initramfs-postmarketos"]
    command += ["-append", '"' + cmdline + '"']
    command += ["-m", str(args.memory)]
    command += ["-redir", "tcp:" + str(args.port) + "::22"]

    if deviceinfo["dtb"] != "":
        dtb_image = rootfs + "/usr/share/dtb/" + deviceinfo["dtb"] + ".dtb"
        if not os.path.exists(dtb_image):
            raise RuntimeError("DTB file not found: " + dtb_image)
        command += ["-dtb", dtb_image]

    if arch == "x86_64":
        command += ["-serial", "stdio"]
        command += ["-drive", "file=" + img_path + ",format=raw"]

    elif arch == "arm":
        command += ["-M", "vexpress-a9"]
        command += ["-sd", img_path]

    elif arch == "aarch64":
        command += ["-M", "virt"]
        command += ["-cpu", "cortex-a57"]
        command += ["-device", "virtio-gpu-pci"]

        # add storage
        command += ["-device", "virtio-blk-device,drive=system"]
        command += ["-drive", "if=none,id=system,file={},id=hd0".format(img_path)]

    else:
        raise RuntimeError("Architecture {} not supported by this command yet.".format(arch))

    # Kernel Virtual Machine (KVM) support
    enable_kvm = True
    if args.arch:
        arch1 = pmb.parse.arch.uname_to_qemu(args.arch_native)
        arch2 = pmb.parse.arch.uname_to_qemu(args.arch)
        enable_kvm = (arch1 == arch2)
    if enable_kvm and os.path.exists("/dev/kvm"):
        command += ["-enable-kvm"]
    else:
        logging.info("Warning: qemu is not using KVM and will run slower!")

    # QXL / SPICE (2D acceleration support)
    if config["enable_spice"]:
        command += ["-vga", "qxl"]
        command += ["-spice",
                    "port={spice_port},addr={spice_addr}".format(**config)
                    + ",disable-ticketing"]

    return command


def run(args):
    """
    Run a postmarketOS image in qemu
    """
    arch = pmb.parse.arch.uname_to_qemu(args.arch_native)
    if args.arch:
        arch = pmb.parse.arch.uname_to_qemu(args.arch)

    device = pmb.parse.arch.qemu_to_pmos_device(arch)
    img_path = system_image(args, device)
    spice_parameters, command_spice = spice_command(args)

    # Workaround: qemu runs as local user and needs write permissions in the
    # system image, which is owned by root
    if not os.access(img_path, os.W_OK):
        pmb.helpers.run.root(args, ["chmod", "666", img_path])

    run_spice = spice_parameters["enable_spice"]
    command = qemu_command(args, arch, device, img_path, spice_parameters)

    logging.info("Running postmarketOS in QEMU VM (" + arch + ")")
    logging.info("Command: " + " ".join(command))
    logging.info("You can login to postmarketOS using SSH:")
    logging.info("ssh -p " + str(args.port) + " user@localhost")
    if not run_spice:
        logging.warning("WARNING: Could not find any SPICE client in your PATH"
                        ", or --no-spice was specified, so Qemu will run"
                        " without some features as 2D acceleration.")
    try:
        process = pmb.helpers.run.user(args, command, background=run_spice)

        # Launch SPICE client
        if run_spice:
            logging.info("Command: " + " ".join(command_spice))
            pmb.helpers.run.user(args, command_spice)
    except KeyboardInterrupt:
        pass
    finally:
        if process:
            process.terminate()
