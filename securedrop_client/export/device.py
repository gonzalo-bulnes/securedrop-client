from tempfile import TemporaryDirectory
from typing import Optional

from .archive import Archive, VirtualFile
from .qvm import QVM


class ConnectedDevice:

    _ARCHIVE_NAME = "usb-test.sd-export"
    _METADATA_FILE_NAME = "metadata.json"
    _METADATA = {"device": "usb-test"}

    __create_key = object()  # Used to ensure the create method is used to construct instances

    @classmethod
    def create(cls, temp_dir: Optional[TemporaryDirectory] = None) -> Optional["ConnectedDevice"]:
        """Creates a ConnectedDevice if a USB device is indeed connected, else None."""

        if temp_dir is not None:
            _temp_dir: TemporaryDirectory = temp_dir
        else:
            _temp_dir = TemporaryDirectory()

        # Try to write to the device to confirm it's connected
        metadata = VirtualFile(cls._METADATA_FILE_NAME, cls._METADATA)
        test_archive = Archive(
            dir_path=str(_temp_dir), name=cls._ARCHIVE_NAME, files=[], virtual_files=[metadata]
        )
        test_archive.save(files_extraction_path="sd-export")

        status = QVM.export(test_archive.path)
        if status != QVM.Status.USB_CONNECTED:
            return None

        device = ConnectedDevice(cls.__create_key)
        return device

    def __init__(self, create_key: object) -> None:
        assert (
            create_key == ConnectedDevice.__create_key
        ), "ConnectedDevice objects must be created using ConnectedDevice.create"


class EncryptedDevice:
    def __init__(self) -> None:
        pass
