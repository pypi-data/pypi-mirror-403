# ----------------------------------------------------------------------------
# Description    : Update file format utilities
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2021)
# ----------------------------------------------------------------------------


# -- include -----------------------------------------------------------------
import configparser
import json
import os
import re
import tarfile
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum, auto
from io import BytesIO, FileIO
from typing import IO, Any, BinaryIO, Callable, Optional, Union

from PySquashfsImage import SquashFsImage

from qblox_instruments.build import DeviceInfo
from qblox_instruments.cfg_man import log
from qblox_instruments.cfg_man.const import VERSION
from qblox_instruments.cfg_man.probe import ConnectionInfo
from qblox_instruments.pnp import CMM_SLOT_INDEX
from qblox_instruments.types import TypeHandle


# ----------------------------------------------------------------------------
class ArchiveType(Enum):
    ZIP = auto()
    TAR_GZ = auto()
    TAR_XZ = auto()
    TAR_BZ2 = auto()
    TAR = auto()
    SQUASHFS = auto()


class ArchiveExtension(Enum):
    ZIP = auto()
    TAR_GZ = auto()
    TAR_XZ = auto()
    TAR_BZ2 = auto()
    TAR = auto()
    RAUC_BUNDLE = auto()


UPDATE_V1_ARCHIVE_TYPES = {
    ArchiveType.TAR,
    ArchiveType.TAR_BZ2,
    ArchiveType.TAR_GZ,
    ArchiveType.TAR_XZ,
    ArchiveType.ZIP,
}


RAUC_MANIFEST_FILE = "manifest.raucm"


class UpdateTarget(Enum):
    """
    Enumeration of update firmware targets.
    """

    QBLOX_OS = auto()
    """
    Qblox-OS update file (raucb format).
    """
    QBLOX_OS_MIGRATION = auto()
    """
    Pulsar-OS to Qblox-OS migration file.
    """
    PULSAR_OS = auto()
    """
    Regular Pulsar-OS update file.
    """


def _is_pulsar_os(
    version: tuple[int, int, int], type_handle: Union[TypeHandle, None] = None
) -> bool:
    """
    Determines if a version tuple represents pulsar-os.

    Parameters
    ----------
    version: tuple[int, int, int]
        Version tuple (major, minor, patch).
    type_handle: TypeHandle
        Optional type handle, which can be passed if the OS can be learned from
        the module type.

    Returns
    -------
    bool
        True if version <= 0.13 (pulsar-os), False if >= 1.0 (qblox-os) or the
        module is a QRC/QSM.

    """
    if type_handle and (type_handle.is_qrc_type or type_handle.is_qsm_type):
        return False
    major, minor, patch = version
    return major == 0 and minor <= 13


def _is_qblox_os(
    version: tuple[int, int, int], type_handle: Union[TypeHandle, None] = None
) -> bool:
    """
    Determines if a version tuple represents qblox-os.

    Parameters
    ----------
    version: tuple[int, int, int]
        Version tuple (major, minor, patch).
    type_handle: TypeHandle
        Optional type handle, which can be passed if the OS can be learned from
        the module type.

    Returns
    -------
    bool
        True if version >= 1.0 (qblox-os) or the module is a QRC/QSM, False if
        <= 0.13 (pulsar-os).

    """
    if type_handle and (type_handle.is_qrc_type or type_handle.is_qsm_type):
        return True
    major, minor, patch = version
    return major >= 1


@dataclass
class UpdateBatch:
    file: BinaryIO
    """
    Binary file-like object for the update file. Will at least be
    opened for reading, and rewound to the start of the file. This may
    effectively be ``open(fname, "rb")``, but could also be a
    ``tempfile.TemporaryFile`` to an update file specifically
    converted to be compatible with the given environment. It is the
    responsibility of the caller to close the file.
    """
    slots: list[int]
    """
    Target slot(s) for this file.
    """
    description: str
    """
    Description for this batch.
    """


@dataclass
class UpdateInfo:
    file: BinaryIO
    """
    Binary file-like object for the update file.
    """
    device: Optional[DeviceInfo] = None
    """
    Target device for this file.
    """


class UpdateFile:
    """
    Representation of a device update file.
    """

    _file: FileIO
    _filename: str

    _update_archive: Any
    _update_file: BinaryIO

    _format: str
    _metadata: Mapping[str, Any]
    _models: Mapping[str, UpdateInfo]
    _has_migrate_folder: bool

    __slots__ = (
        "_file",
        "_filename",
        "_format",
        "_has_migrate_folder",
        "_metadata",
        "_models",
        "_update_archive",
        "_update_file",
    )

    # ------------------------------------------------------------------------
    def __init__(self, file: Union[FileIO, str]) -> None:
        """
        Load an update file.

        Parameters
        ----------
        fname: Union[FileIO, str]
            If specified, file or filename to load.

        """
        self._file = None
        self._filename = None
        self._update_archive = None
        self._update_file = None
        self._has_migrate_folder = False

        self.parse(file)

    def parse(self, file: Union[FileIO, str]) -> None:
        """
        Load update file.

        Parameters
        ----------
        file: Optional[str]
            File or filename to load.

        """
        # Save file and filename
        if isinstance(file, str):
            self._filename = file
            self._file = open(file, "rb")  # noqa: SIM115
        else:
            self._filename = file.name
            self._file = file

        # Determine file types and extensions
        archive_type = _detect_archive_type_magic(self._file)
        archive_extension = _detect_archive_extension(self._filename)

        if archive_type in UPDATE_V1_ARCHIVE_TYPES:
            self._parse_v1()
        elif (
            archive_type == ArchiveType.SQUASHFS
            and archive_extension == ArchiveExtension.RAUC_BUNDLE
        ):
            self._parse_v2()
        else:
            raise ValueError(f"{self._filename}: unknown update file format")

    def _parse_v1(self) -> None:
        self._parse_v1_nested()

        # Read the tar file.
        try:
            log.debug(f"{self._filename}: scanning update tar file...")
            self._update_archive = tarfile.TarFile.open(fileobj=self._update_file, mode="r:gz")
            formats: set[str] = set()
            meta_json = None
            models: dict[str, BinaryIO] = {}
            metadata: dict[str, Any] = {}
            for info in self._update_archive:
                if info is None:
                    break
                name = info.name
                log.debug("  %s", name)

                if info.isdir():
                    path_parts = re.split(r"/|\\", name.lower())
                    if "migration" in path_parts or "migrate" in path_parts:
                        self._has_migrate_folder = True
                        formats.add("multi")

                if name.startswith("."):
                    name = name[1:]
                if name.startswith("/") or name.startswith("\\"):
                    name = name[1:]
                name, *tail = re.split(r"/|\\", name, maxsplit=1)
                if name == "meta.json" and not tail:
                    formats.add("multi")
                    meta_json = info
                elif name.startswith("only_"):
                    name = name[5:]
                    if name not in models:
                        formats.add("multi")
                        metadata[name] = {
                            "manufacturer": "qblox",
                            "model": name,
                        }
                        models[name] = self._update_file
                elif name == "common":
                    formats.add("multi")
                elif _detect_archive_extension(info.name) == ArchiveExtension.RAUC_BUNDLE:
                    sqfs = self._update_archive.extractfile(info.name)
                    if _detect_archive_type_magic(sqfs) == ArchiveType.SQUASHFS:
                        rauc_model = self._parse_rauc(sqfs)
                        models[rauc_model] = sqfs
                        formats.add("raucb")

            log.debug("Scan complete")

            if meta_json is not None:
                with self._update_archive.extractfile(meta_json) as f:
                    metadata.update(json.loads(f.read()))
            self._parse_metadata(formats, metadata, models)

        except tarfile.TarError as err:
            log.debug(f"Error while trying to open {self._filename} as tar file.\n{err}")
            raise ValueError(f"{self._filename}: invalid update file: {err}")

        # Check client version.
        if self._metadata.get("meta", {}).get("min_cfg_man_client", (0, 0, 0)) > VERSION:
            raise NotImplementedError(
                "update file format is too new. Please update Qblox Instruments first"
            )

    def _parse_v1_nested(self) -> None:
        log.debug(f"{self._filename}: determining file type...")
        try:
            tar_archive = tarfile.TarFile.open(fileobj=self._file, mode="r:*")
            for name in tar_archive.getnames():
                if name == "update.tar.gz" or name.endswith("/update.tar.gz"):
                    log.debug(f"{self._filename}: nested .tar file.")
                    self._update_archive = tar_archive
                    self._update_file = self._update_archive.extractfile(name)
                    break
            else:
                log.debug(f"{self._filename}: real update file.")
                self._update_file = self._file
            self._update_file.seek(0)
        except tarfile.TarError as err:
            log.debug(f"{self._filename}: invalid .tar.file: {err}")
            self._file.seek(0)
            try:
                zip_archive = zipfile.ZipFile(self._file, "r")
                for name in zip_archive.namelist():
                    if name == "update.tar.gz" or name.endswith("/update.tar.gz"):
                        log.debug(f"{self._filename}: nested .zip file.")
                        self._update_archive = zip_archive
                        self._update_file = self._update_archive.open(name)
                        break
            except zipfile.BadZipFile as err:
                log.debug(f"{self._filename}: invalid .zip file: {err}")

        if self._update_file is None:
            raise ValueError(f"{self._filename}: invalid update file")

    def _parse_v2(self) -> None:
        model = self._parse_rauc(self._file)
        self._has_migrate_folder = False
        self._parse_metadata(
            formats={"raucb"},
            metadata={},
            models={model: self._file},
        )

    def _parse_rauc(self, file: BinaryIO) -> str:
        image = SquashFsImage(file)
        manifest_entry = image.find("manifest.raucm")
        if manifest_entry is None:
            raise ValueError("No manifest in RAUC bundle")

        manifest = _parse_rauc_manifest(BytesIO(manifest_entry.read_bytes()))
        file.seek(0)
        return manifest["update"]["compatible"]

    def _parse_metadata(
        self, formats: set[str], metadata: dict[str, Any], models: dict[str, BinaryIO]
    ) -> None:
        if len(formats) != 1:
            raise ValueError("invalid update file")
        self._format = next(iter(formats))
        self._metadata = metadata.get("meta", {})
        self._models = {
            model: UpdateInfo(
                file=file,
                device=DeviceInfo.from_dict(metadata[model]) if model in metadata else None,
            )
            for model, file in sorted(models.items())
        }

    # ------------------------------------------------------------------------
    def close(self) -> None:
        """
        Cleans up any operating resources that we may have claimed.
        """
        if hasattr(self, "_tempdir") and self._tempdir is not None:
            self._tempdir.cleanup()
            self._tempdir = None

    # ------------------------------------------------------------------------
    def __del__(self) -> None:
        self.close()

    # ------------------------------------------------------------------------
    def __enter__(self) -> "UpdateFile":
        return self

    # ------------------------------------------------------------------------
    def __exit__(self, exc_type, exc_value, traceback) -> Optional[bool]:
        self.close()

    # ------------------------------------------------------------------------
    def needs_confirmation(self) -> Optional[str]:
        """
        Returns whether the update file requests the user to confirm something
        before application, and if so, what message should be printed.

        Returns
        -------
        Optional[str]
            None if there is nothing exceptional about this file, otherwise
            this is the confirmation message.

        """
        return self._metadata.get("confirm", None)

    # ------------------------------------------------------------------------
    def __str__(self) -> str:
        return self._filename

    # ------------------------------------------------------------------------
    def __repr__(self) -> str:
        return repr(self._filename)

    # ------------------------------------------------------------------------
    def summarize(self) -> str:
        """
        Returns a summary of the update file format.

        Returns
        -------
        str
            Update file summary.

        """
        return f"update file for {', '.join(self._models)}"

    # ------------------------------------------------------------------------
    def pprint(self, output: Callable[[str], None] = log.info) -> None:
        """
        Pretty-prints the update file metadata.

        Parameters
        ----------
        output: Callable[[str], None]
            The function used for printing. Each call represents a line.

        """
        min_client = self._metadata.get("min_cfg_man_client", None)
        if min_client is not None:
            min_client = ".".join(map(str, min_client))

        query_message = self._metadata.get("confirm", "None")

        output(f"Update file              : {self._filename}")
        output(f"File format              : {self._format}")
        output(f"Minimum client version   : {min_client}")
        output(f"Query message            : {query_message}")
        output(f"Contains updates for     : {len(self._models)} product(s)")
        for model, info in self._models.items():
            output(f"  Model                  : {model}")
            for key, pretty in (
                ("sw", "Application"),
                ("fw", "FPGA firmware"),
                ("kmod", "Kernel module"),
                ("cfg_man", "Cfg. manager"),
            ):
                if info.device is not None and key in info.device:
                    output(f"    {pretty + ' version':<21}: {info.device[key]}")

    # ------------------------------------------------------------------------
    def load(
        self,
        ci: ConnectionInfo,
        included_slots: Optional[Iterable[int]] = None,
        excluded_slots: Optional[Iterable[int]] = None,
    ) -> list[UpdateBatch]:
        """
        Loads an update file, checking whether the given update file is
        compatible within the given connection context. Returns a list of
        update batches to be run, each containing a file-like object and
        a target slot list, or throws a ValueError if there is a problem.

        Parameters
        ----------
        ci: ConnectionInfo
            Connection information object retrieved from autoconf(), to verify
            that the update file is compatible, or to make it compatible, if
            possible.
        included_slots: Optional[Iterable[int]]
            list of included slot indices. Optional, by default None.
        excluded_slots: Optional[Iterable[int]]
            list of excluded slot indices. Optional, by default None.

        Returns
        -------
        list[UpdateBatch]
            List of update batches to run, each containing

        Raises
        ------
        ValueError
            If there is a problem with the given update file.

        """
        # Check whether the update includes data for all the devices we need to
        # support.
        log.info(f"Models In Cluster        : {sorted(ci.all_updatable_models)}")
        log.info(f"Models In Update Package : {sorted(set(self._models.keys()))}")

        if ci.slot_index is not None:
            # Single slot update
            log.info(f"Single-Slot Update in slot {ci.slot_index}")
            model = next(iter(ci.all_updatable_models))
            slot_no = int(ci.slot_index)
            slot_models = {slot_no: model}
        else:
            # Multiple slots update
            log.info("Multi-Slot Update")
            slot_models = {int(slot): module.model for slot, module in ci.device.modules.items()}
            if CMM_SLOT_INDEX not in slot_models:
                slot_models[CMM_SLOT_INDEX] = "cluster_mm"

        # Handle in- and exclusions
        if excluded_slots is not None:
            slot_models = {
                slot: model for slot, model in slot_models.items() if slot not in excluded_slots
            }
        if included_slots is not None:
            slot_models = {
                slot: model for slot, model in slot_models.items() if slot in included_slots
            }

        # Check compatibility and build model list
        incompatible_models = set()
        models: dict[str, list[int]] = {}
        for slot, model in slot_models.items():
            if model not in ci.all_updatable_models:
                continue
            if model not in self._models:
                incompatible_models.add(model)
            models.setdefault(model, []).append(slot)

        # FIXME: Skip QSM in the case that there is one in the cluster but no update file for it
        if "cluster_qsm" in incompatible_models:
            log.warn("QSM not present in update file, skipping...")
            incompatible_models.remove("cluster_qsm")  # won't raise a ValueError below
            models.pop("cluster_qsm", None)  # won't be included in update batches

        incompatible_models = list(sorted(incompatible_models))
        if incompatible_models:
            if len(incompatible_models) == 1:
                to_print = incompatible_models[0]
            else:
                to_print = ", ".join(incompatible_models[:-1]) + " and " + incompatible_models[-1]
            raise ValueError(f"update file is not compatible with {to_print} devices")

        # Now build update batches!
        batches = {}
        for model, slots in models.items():
            update_info = self._models[model]
            # If different models use the same update files, merge them
            if id(update_info.file) in batches:
                batch = batches[id(update_info.file)]
            else:
                batch = UpdateBatch(file=update_info.file, slots=[], description="")
            batch.slots.extend(slots)
            if batch.description:
                batch.description += ", " + model
            else:
                batch.description = model
            batches[id(update_info.file)] = batch

        # Update cluster_mm last
        return list(sorted(batches.values(), key=lambda b: "cluster_mm" in b.description))

    def get_update_type(self) -> UpdateTarget:
        """
        Determines the type of update file.

        Returns
        -------
        UpdateTarget
            The type of update file:

            - QBLOX_OS (qblox-os update),
            - MIGRATION (pulsar-os to qblox-os migration),
            - PULSAR_OS (regular pulsar-os update).

        """
        if self._format == "raucb":
            return UpdateTarget.QBLOX_OS
        if self._has_migrate_folder:
            return UpdateTarget.QBLOX_OS_MIGRATION
        return UpdateTarget.PULSAR_OS


def _detect_archive_type_magic(file_obj: IO[bytes]) -> Optional[ArchiveType]:
    """
    Detect archive/image type based on magic bytes.

    Parameters
    ----------
    filepath: str
        The file to load.

    Returns
    -------
    ArchiveType
        An Enum with the different file types or None if not supported.

    """
    if not file_obj.seekable():
        return None

    pos = file_obj.tell()
    file_obj.seek(0)
    header = file_obj.read(264)
    file_obj.seek(pos)

    magic_type: Optional[ArchiveType] = None
    if header.startswith(b"\x50\x4b\x03\x04"):
        magic_type = ArchiveType.ZIP
    elif header.startswith(b"\x1f\x8b"):
        magic_type = ArchiveType.TAR_GZ
    elif header.startswith(b"\xfd\x37\x7a\x58\x5a\x00"):
        magic_type = ArchiveType.TAR_XZ
    elif header.startswith(b"\x42\x5a\x68"):
        magic_type = ArchiveType.TAR_BZ2
    elif header.startswith(b"hsqs"):
        # squashfs of rauc bundles has 'hsqs' ie 0x73717368 magic number
        magic_type = ArchiveType.SQUASHFS
    elif len(header) >= 262 and (header[257:262] in [b"ustar", b"ustar\x00"]):
        # Tar files do not have a fixed magic at the beginning,
        # but the ustar signature is at byte offset 257
        magic_type = ArchiveType.TAR

    return magic_type


def _detect_archive_extension(filepath: str) -> Optional[ArchiveExtension]:
    """
    Detects the archive type based on file extension.

    Parameters
    ----------
    filepath: str
        The file to load.

    Returns
    -------
    ArchiveExtension
        An Enum file extension type, 'zip', 'tar.gz', 'tar.xz', 'tar.bz2', 'tar', 'raucb'
        or None if not supported

    """
    filename = os.path.basename(filepath).lower()

    extension = None
    if filename.endswith((".zip",)):
        extension = ArchiveExtension.ZIP
    elif filename.endswith((".tar.gz", ".tgz")):
        extension = ArchiveExtension.TAR_GZ
    elif filename.endswith((".tar.xz", ".txz")):
        extension = ArchiveExtension.TAR_XZ
    elif filename.endswith((".tar.bz2", ".tbz2")):
        extension = ArchiveExtension.TAR_BZ2
    elif filename.endswith((".tar",)):
        extension = ArchiveExtension.TAR
    elif filename.endswith((".raucb",)):
        extension = ArchiveExtension.RAUC_BUNDLE

    return extension


def _parse_rauc_manifest(fobj: BinaryIO) -> Mapping[str, Any]:
    config = configparser.ConfigParser()
    config.read_string(fobj.read().decode("utf-8"))
    return config
