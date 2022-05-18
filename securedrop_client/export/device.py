from tempfile import TemporaryDirectory
from typing import Optional

from .archive import Archive, VirtualFile
from .qvm import QVM


class ConnectedDevice:

    # These are part of the export service API
    _ARCHIVE_NAME = "usb-test.sd-export"
    _METADATA_FILE_NAME = "metadata.json"
    _METADATA = {"device": "usb-test"}
    _FILES_EXTRACTION_PATH = "sd-export"

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
        test_archive = Archive(files=[], virtual_files=[metadata])
        test_archive_on_disk = test_archive.save(
            dir_path=_temp_dir.name,
            name=cls._ARCHIVE_NAME,
            files_extraction_path=cls._FILES_EXTRACTION_PATH,
        )

        status = QVM.export(test_archive_on_disk.path)
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
