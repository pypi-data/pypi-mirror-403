# ----------------------------------------------------------------------------
# Description    : "Smart" automatic configuration for connecting to a host
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2021)
# ----------------------------------------------------------------------------


# -- include -----------------------------------------------------------------

import json
from collections import namedtuple
from typing import Callable, Optional, Union

from qblox_instruments.build import DeviceInfo, get_build_info
from qblox_instruments.cfg_man import log
from qblox_instruments.ieee488_2 import IpTransport
from qblox_instruments.pnp import (
    CMM_SLOT_INDEX,
    PNP_PORT,
    AddressInfo,
    PlugAndPlay,
    resolve,
)
from qblox_instruments.scpi.layers.cfg_man import CfgMan

# -- probe_port() ------------------------------------------------------------

# Result of probe_port()
PortInfo = namedtuple("PortInfo", ["protocol", "version", "device"])

PortInfo.__doc__ = """
Protocol information for a particular IP/TCP port pair, supporting SCPI
configuration manager protocol.
"""

PortInfo.protocol.__doc__ = """
:str: The type of host we're connected to, which will be one of the following
values.

   ``update()`` function from this file can be used to update the
   device, but other features will not work (use an older
   configuration manager if you need them).
 - ``"cfg_man"``: the configuration manager application via SCPI.
   This application can manage the device at the given host, but
   only that device.
 - ``"app"``: the instrument application via SCPI. This means the
   connection is fully-featured, including the ability to configure
   modules (if this is a CMM).
"""

PortInfo.version.__doc__ = """
:str: Configuration manager server version.
"""

PortInfo.device.__doc__ = """
:DeviceInfo: Device information structure.
"""


# ----------------------------------------------------------------------------
def probe_port(
    host: str,
    port: int,
    timeout: float = 10.0,
    slot: Optional[int] = None,
) -> PortInfo:
    """
    Automatically detects what type of application is listening on the given
    host and port.

    Parameters
    ----------
    host: str
        IP address or hostname of the server to connect to.
    port: int
        Port to connect to.
    timeout: float
        Socket timeout in seconds.
    slot: int, Optional
        Slot number to use for the connection via CMM. If `None`, uses port for
        the connection

    Returns
    -------
    PortInfo
        Information about the protocol.

    Raises
    ------
    ConnectionError
        If the configuration manager returned something we didn't expect or
        connection failed.

    """
    protocol = "unknown"
    device = None
    server_version = (0, 0, 0)

    try:
        # Attempt to use the `*DESCribe?` SCPI command to obtain detailed
        # device information.
        with IpTransport(host, port, timeout) as transport:
            cm = CfgMan(transport)
            description = cm.get_json_description()

            if description:
                try:
                    # Extract version info for specific slots if requested
                    if slot not in (None, CMM_SLOT_INDEX):
                        modules = description.get("modules", {})
                        module_description = modules.get(str(slot), {})
                        if module_description.get("is_extended_instrument", False):
                            server_version = description.get("cfg_man", {}).get(
                                "version", (0, 0, 0)
                            )
                        device = DeviceInfo.from_dict(module_description)
                    else:
                        device = DeviceInfo.from_dict(description)
                except (KeyError, TypeError, ValueError):
                    # If the description dict is malformed, discard it and force `*IDN?` fallback
                    device = None

            if device is None:
                # If it fails, fallback to `*IDN?`
                idn = cm._get_idn()
                device = DeviceInfo.from_idn(idn)

                # Get the modules too.
                mods_info_bin = cm._read_bin("*MODS?")
                mods_info = json.loads(mods_info_bin.decode("utf-8"))
                mods_info = {
                    slot_str: (mod.get("IDN", "") if isinstance(mod, dict) else str(mod))
                    for slot_str, mod in mods_info.items()
                }
                device.set_modules_from_idn(mods_info)

                if slot not in (None, CMM_SLOT_INDEX):
                    slot_str = str(slot)
                    if device.modules and slot_str in device.modules:
                        module = device.modules[slot_str]
                        if module.is_extended_instrument:
                            server_version = device.cfg_man_build.version

                        device = module
                    else:
                        raise ConnectionError(
                            f"Slot {slot} not found in device modules via *MODS?."
                        )

    except OSError as err:
        raise ConnectionError(f"Failed to connect to {host}:{port}. Error: {err}") from err
    except Exception as err:
        raise ConnectionError(f"Protocol detection failed due to unexpected error: {err}") from err

    if device:
        if "cfg_man" in device:
            server_version = device.cfg_man_build.version
            protocol = "app" if "sw" in device else "cfg_man"
        elif device.is_extended_instrument:
            protocol = "app"
        else:
            raise ConnectionError("Received unexpected response during protocol detection")
    else:
        raise ConnectionError("Failed to obtain device identity (No IDN or description received)")

    return PortInfo(protocol, server_version, device)


# -- probe_device() ----------------------------------------------------------

# Result of probe_device()
ConnectionInfo = namedtuple(
    "ConnectionInfo",
    [
        "identifier",
        "protocol",
        "address",
        "slot_index",
        "ip_config",
        "server_version",
        "device",
        "all_updatable_models",
    ],
)

ConnectionInfo.__doc__ = """
Configuration manager connection information structure.
"""

ConnectionInfo.identifier.__doc__ = """
:Union[str, AddressInfo]: Device identifier or address, as passed to
:func:`~probe_device()`.
"""

ConnectionInfo.protocol.__doc__ = """
:str: The protocol that must be used to connect. Can be:

 - ``"scpi"`` for the SCPI-based configuration manager protocol; or
 - ``"pnp"`` when the device is not accessible due to IP address
   misconfiguration.
"""

ConnectionInfo.address.__doc__ = """
:Union[str, tuple[str, int]]: Two-tuple of the IP address and port we need to
use to connect for SCPI connections, or the device serial number
for plug & play.
"""

ConnectionInfo.slot_index.__doc__ = """
:Optional[int]: None for entire device, slot index if only a single module in
the device will be affected.
"""

ConnectionInfo.ip_config.__doc__ = """
:str: The IP configuration of the device that will be applied when the device
is rebooted, if known. May or may not match the address field, as the
configuration may have changed since the instrument was last rebooted, and the
local IP address of the instrument may differ from what we're connecting to if
NAT is involved.
"""

ConnectionInfo.server_version.__doc__ = """
:Optional[tuple[int, int, int]]: Configuration manager server version, if
known. Will be None for plug & play.
"""

ConnectionInfo.device.__doc__ = """
:DeviceInfo: Device information structure.
"""

ConnectionInfo.all_updatable_models.__doc__ = """
:set[str]: Set of lowercase model names that will need to be present in the
update package. Must include ``{device}``, but the cluster management module
may for instance request more model names.
"""


# ----------------------------------------------------------------------------
def represent_address(ci: ConnectionInfo) -> str:
    """
    Returns a human-readable string representation of the address.

    Parameters
    ----------
    ci: ConnectionInfo
        The connection information object to represent the address of.

    Returns
    -------
    str
        String representation of the address.

    """
    if ci.protocol == "pnp":
        address = ci.address
    elif ":" in ci.address[0]:
        address = "[{}]:{}".format(*ci.address)
    else:
        address = "{}:{}".format(*ci.address)
    return address


# ----------------------------------------------------------------------------
def represent_connection(ci: ConnectionInfo) -> str:
    """
    Returns a human-readable string representation of the connection.

    Parameters
    ----------
    ci: ConnectionInfo
        The connection information object to represent the connection of.

    Returns
    -------
    str
        String representation of the connection.

    """
    return "{} using {}".format(
        represent_address(ci),
        {
            "pnp": "Qblox plug & play only (IP & name configuration only)",
            "scpi": "SCPI",
        }.get(ci.protocol, "?"),
    )


# ----------------------------------------------------------------------------
def represent_device(ci: ConnectionInfo) -> str:
    """
    Returns a human-readable string representation of the device we're
    connecting to.

    Parameters
    ----------
    ci: ConnectionInfo
        The connection information object to represent the device of.

    Returns
    -------
    str
        String representation of the device.

    """
    info_parts = []
    if ci.device.serial is not None:
        info_parts.append(f"serial {ci.device.serial}")
    if ci.device.name is not None:
        info_parts.append(f"name {ci.device.name}")
    info = f", with {' and '.join(info_parts)}" if info_parts else ""
    return (
        f"{ci.device} at address {represent_address(ci)} "
        f"({'whole instrument' if ci.slot_index is None else f'only slot {ci.slot_index}'}){info}"
    )


# ----------------------------------------------------------------------------
def pprint_connection_info(ci: ConnectionInfo, output: Callable[[str], None] = log.info) -> None:
    """
    Pretty-prints information about a connection information object.

    Parameters
    ----------
    ci: ConnectionInfo
        The connection information object to pretty-print.
    output: Callable[[str], None]
        The function used for printing. Each call represents a line.

    """
    # Format address.
    if ci.protocol == "pnp":
        address = ci.address
        port = PNP_PORT
    else:
        address, port = ci.address

    # Format protocol.
    protocol = "{}{}".format(
        {
            "pnp": "Qblox plug & play only (IP & name configuration only), via UDP broadcast port ",
            "scpi": "SCPI, via TCP port ",
        }.get(ci.protocol, "?"),
        port,
    )

    # Format scope.
    if ci.slot_index is None:
        scope = "entire instrument"
    elif ci.slot_index == 0:
        scope = "only the cluster management module"
    else:
        scope = f"only the module in slot {ci.slot_index}"

    # Format server version.
    server_version = "n/a" if ci.server_version is None else ".".join(map(str, ci.server_version))

    # Format submodule model names.
    submodule_models = ", ".join(
        (
            ci.all_updatable_models
            if ci.device.modules is None
            else {module.model for module in ci.device.modules.values()}
        )
        - {ci.device.model}
    )
    if not submodule_models:
        submodule_models = "n/a"

    # Print connection information.
    output(f"Connecting to            : {address}")
    output(f"Via protocol             : {protocol}")
    output(f"Configuration scope      : {scope}")
    output(f"Server version           : {server_version}")
    output(f"Client version           : {get_build_info().version_str}")
    output("-------------------------:-------------------------")
    output(f"Device type              : {ci.device}")
    output(f"Device name              : {ci.device.name}")
    output(f"Serial number            : {ci.device.serial}")
    if ci.device.mac_address:
        output(f"Mac address              : {ci.device.mac_address}")
    output(f"IP configuration         : {ci.ip_config}")
    output(f"Submodule types          : {submodule_models}")
    for key, pretty in (
        ("sw", "Application"),
        ("fw", "FPGA firmware"),
        ("kmod", "Kernel module"),
        ("cfg_man", "Config. manager"),
    ):
        if key in ci.device:
            output(f"{pretty + ' version':<25}: {ci.device[key]}")


# ----------------------------------------------------------------------------
def connection_info_to_json(ci: ConnectionInfo) -> dict:
    """
    Converts a ConnectionInfo object to a JSON-serializable representation
    thereof.

    Parameters
    ----------
    ci: ConnectionInfo
        The connection information object to pretty-print.

    Returns
    -------
    dict
        A structure using only JSON-serializable types with all the information
        of the ConnectionInfo object in it.

    """
    d = ci._asdict()
    d["device"] = d["device"].to_dict()
    d["all_updatable_models"] = list(d["all_updatable_models"])
    return d


# ----------------------------------------------------------------------------
def probe_device(
    identifier: Union[str, AddressInfo, ConnectionInfo], quiet: bool = False
) -> ConnectionInfo:
    """
    Automatically detects how to manage the given device.

    Parameters
    ----------
    identifier: str
        Instrument identifier. See :func:`~qblox_instruments.resolve()` for
        more information.
    quiet: bool
        When set, don't log anything.

    Returns
    -------
    ConnectionInfo
        The detected connection and device information.

    Raises
    ------
    RuntimeError
        if we failed to connect.

    """
    # Fallthrough if input is already a resolved configuration structure.
    if isinstance(identifier, ConnectionInfo):
        return identifier

    # Figure out how to connect to the device with the given identifier.
    info = resolve(identifier)
    protocol = info.protocol
    address = info.address
    slot_index = info.slot_index
    app_port = info.scpi_port
    cfg_port = info.cfg_port

    # Load default return values.
    full_address = address
    ip_config = "unknown"
    server_version = None
    device = None
    all_updatable_models = set()
    fall_back_to_cmm = False

    # Handle the case where we can only connect via plug & play.
    if protocol == "pnp":
        # Get device information via plug & play.
        with PlugAndPlay() as p:
            description = p.describe(identifier).get("description", {})

        # Parse build information.
        device = DeviceInfo.from_dict(description)
        all_updatable_models.add(device.model)

    elif protocol == "ip":
        # Preferentially connect to the application.
        fall_back_to_cfg_man = False
        fall_back_to_cmm = False

        # Try to connect to the application running on the device with a
        # short timeout (since it's acceptable if we can't connect to it).
        if not quiet:
            log.info("Trying to connect to application (port %d)...", app_port)
        info = None
        try:
            info = probe_port(address, app_port, 1.0)
        except Exception as e:
            fall_back_to_cfg_man = True
            if not quiet:
                log.info(
                    "Failed to connect to application (%s), falling back to cfg_man.",
                    e,
                )
        if info is not None:
            # We can connect to the application. Update device information
            # from what we've learned from this.
            protocol = "scpi"
            full_address = (address, app_port)
            server_version = info.version
            device = info.device
            all_updatable_models.add(device.model)

            # Fall back anyway if we're only supposed to affect the module
            # we're directly connected to, and not any of the submodules
            # controlled by it.
            if slot_index == CMM_SLOT_INDEX:
                fall_back_to_cfg_man = True
                if not quiet:
                    log.info(
                        "Application is responsive, but connecting to "
                        "configuration manager anyway, such that only the "
                        "management module is updated."
                    )

        # Fall back to configuration manager if needed.
        if fall_back_to_cfg_man:
            if not quiet:
                log.info("Trying to connect to configuration manager (port %d)...", cfg_port)

            info = None
            try:
                info = probe_port(address, cfg_port, 3.0)
            except Exception as e:
                fall_back_to_cmm = True
                if slot_index is None:
                    raise RuntimeError(
                        f'Failed to connect to "{identifier}", determined to be at {address}.'
                    )
                if not quiet:
                    log.info(
                        "Failed to connect to configuration manager (%s), falling back to CMM.",
                        e,
                    )
            if info is not None:
                # Update connection information.
                protocol = "scpi"
                full_address = (address, cfg_port)
                server_version = info.version
                if device is None:
                    device = info.device
                else:
                    description = device.to_dict()
                    description.update(info.device.to_dict())
                    device = DeviceInfo.from_dict(description)
                all_updatable_models.add(device.model)
            # If connection to the configuration manager fails and slot_index is
            # provided, try to reach via CMM.
            if fall_back_to_cmm and slot_index is not None:
                try:
                    # Resolve the CMM address and port.
                    info = resolve(address)
                    address = info.address
                    app_port = info.scpi_port
                    if not quiet:
                        log.info("Trying to connect to application (port %d)...", app_port)
                    # Connect to CMM and retrieve module information.
                    info = probe_port(address, app_port, 1.0, slot_index)
                    protocol = "scpi"
                    full_address = (address, app_port)
                    server_version = info.version
                    device = info.device
                    all_updatable_models.add(device.model)
                except Exception as e:
                    if not quiet:
                        log.info("Failed to connect to CMM application (%s)", e)
                    raise RuntimeError(
                        f"Failed to connect to CMM application ({e}), which was "
                        f"determined to be at '{identifier}'."
                    )
    else:
        assert False

    # Get some additional information if this is a fully-featured SCPI
    # connection.
    if protocol == "scpi" and not fall_back_to_cmm:
        with IpTransport(full_address[0], full_address[1], 3.0) as t:
            cm = CfgMan(t)

            # Read name from device.
            if device.name == "unknown":
                device.update_name(cm.get_name())

            # Read current IP configuration from device.
            ip_config = cm.get_ip_config()

            # Read module types.
            module_types = cm._get_update_module_types()
            if module_types != "not_applicable":
                all_updatable_models.update(module_types.split(","))

    # Warn if the user is trying to configure only the cluster management
    # module of a cluster, when the device we're connecting to is not a
    # cluster management module.
    if slot_index == CMM_SLOT_INDEX and device.model != "cluster_mm":
        if not quiet:
            log.warn(
                "Scope was restricted to the cluster management module, but "
                "the device we're connecting to is not a cluster."
            )
        slot_index = None

    # Add the module suffix back onto the identifier.
    if slot_index is not None:
        identifier = f"{identifier}/{slot_index}"

    # Build and return connection information structure.
    return ConnectionInfo(
        identifier,
        protocol,
        full_address,
        slot_index,
        ip_config,
        server_version,
        device,
        all_updatable_models,
    )


# ----------------------------------------------------------------------------
def get_device_info(identifier: Union[str, AddressInfo, ConnectionInfo]) -> DeviceInfo:
    """
    Fetches a complete :class:`~qblox_instruments.DeviceInfo` structure for
    the given device.

    Parameters
    ----------
    identifier: Union[str, AddressInfo, ConnectionInfo]
        Instrument identifier. See :func:`~qblox_instruments.resolve()` for
        more information.

    Returns
    -------
    DeviceInfo
        The device information.

    Raises
    ------
    RuntimeError
        if we failed to connect.

    """
    return probe_device(identifier, quiet=True).device
