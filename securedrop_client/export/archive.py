import json
import os
import tarfile
from io import BytesIO
from typing import List, Optional


class File:
    """A file to be added to an archive."""

    def __init__(self, path: str) -> None:
        self._name = os.path.basename(path)
        self._path = path

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path


class VirtualFile:
    """Data to create a file into an archive."""

    def __init__(self, name: str, data: dict) -> None:
        self._name = name
        self._data = data

    @property
    def name(self) -> str:
        return self._name

    @property
    def data(self) -> dict:
        return self._data


class Archive:
    """An archive that can be saved to disk."""

    def __init__(self, files: List[File], virtual_files: List[VirtualFile]) -> None:
        super().__init__()
        self._files: List[File] = files
        self._virtual_files: List[VirtualFile] = virtual_files

    @property
    def files(self) -> List[File]:
        return self._files

    @property
    def virtual_files(self) -> List[VirtualFile]:
        return self._virtual_files

    def save(self, dir_path: str, name: str, files_extraction_path: str) -> "ArchiveOnDisk":
        """Organize the files, create the virtual files and write the archive to disk."""
        return ArchiveOnDisk(dir_path, name, files_extraction_path, data=self)


class ArchiveOnDisk:
    """An archive that was saved to disk."""

    def __init__(self, dir_path: str, name: str, files_extraction_path: str, data: Archive) -> None:
        super().__init__()

        self._path = os.path.join(dir_path, name)
        self._data_on_disk: Optional[tarfile.TarFile] = None

        with tarfile.open(self._path, "w:gz") as archive:
            self._data_on_disk = archive
            for vf in data.virtual_files:
                self._write_virtual_file(vf)
            for f in data.files:
                self._write_file(f, files_extraction_path)

    @property
    def path(self) -> str:
        return self._path

    def _write_virtual_file(self, f: VirtualFile) -> None:
        """
        Create a file with the given name and data, directly into the on-disk archive.
        """
        if self._data_on_disk is None:
            return
        filedata_string = json.dumps(f.data)
        filedata_bytes = BytesIO(filedata_string.encode("utf-8"))
        tarinfo = tarfile.TarInfo(f.name)
        tarinfo.size = len(filedata_string)
        self._data_on_disk.addfile(tarinfo, filedata_bytes)

    def _write_file(self, f: File, extraction_path: str) -> None:
        """
        Add the file to the on-disk archive.

        When the archive is extracted, the file will be
        contained is a directory that matches extraction_path.
        """
        if self._data_on_disk is None:
            return
        arcname = os.path.join(extraction_path, f.name)
        self._data_on_disk.add(f.path, arcname=arcname, recursive=False)
