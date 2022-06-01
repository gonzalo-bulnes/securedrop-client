from tempfile import TemporaryDirectory
from typing import Dict, List, Optional

from ..archive import Archive as GenericArchive
from ..archive import ArchiveOnDisk, File, VirtualFile
from ..qvm import QVM


class Archive:
    """An archive with adequate structure and metadata for exporting files to a USB disk."""

    # These are part of the export service API
    _ARCHIVE_NAME = "archive.sd-export"
    _METADATA_FILE_NAME = "metadata.json"
    _METADATA = {"device": "disk", "encryption_method": "luks"}
    _FILES_EXTRACTION_PATH = "export_data"
    _DISK_ENCRYPTION_KEY_NAME = "encryption_key"

    def __init__(self, files: List[File], disk_encryption_passphrase: str) -> None:
        super().__init__()

        self._passphrase = disk_encryption_passphrase

        # Create and archive with adequate metadata
        metadata = VirtualFile(self._METADATA_FILE_NAME, self._metadata)
        self._data = GenericArchive(files=files, virtual_files=[metadata])

    @property
    def _metadata(self) -> Dict[str, str]:
        metadata = self._METADATA.copy()
        metadata[self._DISK_ENCRYPTION_KEY_NAME] = self._passphrase
        return metadata

    def _save(self, temp_dir: Optional[TemporaryDirectory] = None) -> ArchiveOnDisk:
        """Create archive on disk with metadata and structure that trigger USB disk export."""
        if temp_dir is not None:
            _temp_dir: TemporaryDirectory = temp_dir
        else:
            _temp_dir = TemporaryDirectory()

        # Persist an archive on disk with adequate structure
        return ArchiveOnDisk(
            dir_path=_temp_dir.name,
            name=self._ARCHIVE_NAME,
            files_extraction_path=self._FILES_EXTRACTION_PATH,
            data=self._data,
        )

    def export(self, temp_dir: Optional[TemporaryDirectory] = None) -> QVM.Status:
        """Send the archive to export VM (sd-devices) for automated USB disk export."""
        exportable_archive = self._save(temp_dir)
        return QVM.open_in_export_vm(exportable_archive.path)
