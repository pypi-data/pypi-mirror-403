"""ImportItem base class and inherited classes"""

import tempfile
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from types import TracebackType
from typing import ClassVar

from cmem_client.models.base import Model


class ImportItem(ABC, Model):
    """Abstract base class for different import source types.

    Each concrete implementation represents a different source type
    (file, directory, zip, etc.) and knows how to prepare itself
    for import by providing a Path to a directory or file.
    """

    import_type: ClassVar[str]

    def __init__(self, source: Path | str) -> None:
        """Initialize the import item with its source.

        Args:
            source: Source path or identifier for the import
        """
        super().__init__()
        self.source = Path(source) if isinstance(source, str) else source
        self._prepared_path: Path | None = None
        self._cleanup_needed: bool = False

    @abstractmethod
    def prepare(self) -> Path:
        """Prepare the import source and return a path to import from.

        This method transforms the source into a format suitable for import.
        For example:
        - Zip files are extracted to a temp directory
        - Directories are returned as-is

        Returns:
            Path to directory or file ready for import
        """

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up any temporary resources created during preparation."""

    def __enter__(self) -> Path:
        """Context manager entry. Prepare the import source."""
        self._prepared_path = self.prepare()
        return self._prepared_path

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit. Cleanup resources."""
        self.cleanup()

    @classmethod
    def detect(cls, source: Path) -> type["ImportItem"]:
        """Detect the appropriate ImportItem type for the given source.

        Args:
            source: Path to analyze

        Returns:
            The appropriate ImportItem subclass
        """
        if source.is_dir():
            return DirectoryImportItem
        if zipfile.is_zipfile(source):
            return ZipImportItem
        return FileImportItem


class DirectoryImportItem(ImportItem):
    """Import from a directory - no transformation needed."""

    import_type = "directory"

    def prepare(self) -> Path:
        """Return directory path as-is."""
        return self.source

    def cleanup(self) -> None:
        """No cleanup needed for directories."""


class FileImportItem(ImportItem):
    """Import from a single file, copy to temp directory."""

    import_type = "file"

    def prepare(self) -> Path:
        """Copy file to a temporary directory."""
        return self.source

    def cleanup(self) -> None:
        """Remove temporary directory."""


class ZipImportItem(ImportItem):
    """Import from a zip archive - extract to temp directory."""

    import_type = "zip"

    def __init__(self, source: Path | str) -> None:
        super().__init__(source)
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None

    def prepare(self) -> Path:
        """Extract zip to temporary directory."""
        self._temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(self._temp_dir.name)
        with zipfile.ZipFile(self.source, "r") as zipf:
            zipf.extractall(temp_path)
        self._cleanup_needed = True
        return temp_path

    def cleanup(self) -> None:
        """Remove temporary directory."""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None


def create_import_item(source: Path) -> ImportItem:
    """Factory function to create appropriate ImportItem instance.

    Args:
        source: Path to the import source

    Returns:
        Appropriate ImportItem instance based on source type
    """
    item_class = ImportItem.detect(source)
    return item_class(source)
