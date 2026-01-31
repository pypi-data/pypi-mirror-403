"""Base class that supports common output data methods and paths."""

import logging
from abc import ABC
from abc import abstractmethod
from functools import cached_property
from pathlib import Path

from dkist_processing_common.models.tags import Tag
from dkist_processing_common.tasks import WorkflowTaskBase
from dkist_processing_common.tasks.mixin.globus import GlobusTransferItem
from dkist_processing_common.tasks.mixin.object_store import ObjectStoreMixin

logger = logging.getLogger(__name__)


class OutputDataBase(WorkflowTaskBase, ABC):
    """Subclass of WorkflowTaskBase which encapsulates common output data methods."""

    @cached_property
    def destination_bucket(self) -> str:
        """Get the destination bucket."""
        return self.metadata_store_recipe_run.configuration.destination_bucket

    def format_object_key(self, path: Path, folder_modifier: str | None = None) -> str:
        """
        Convert output paths into object store keys.

        Parameters
        ----------
        path: the Path to convert
        folder_modifier: optional folder name to insert into the path

        Returns
        -------
        formatted path in the object store
        """
        if folder_modifier:
            object_key = self.destination_folder / Path(folder_modifier) / Path(path.name)
        else:
            object_key = self.destination_folder / Path(path.name)
        return str(object_key)

    @property
    def destination_folder(self) -> Path:
        """Format the destination folder."""
        return self.destination_root_folder / Path(self.constants.dataset_id)

    @property
    def destination_root_folder(self) -> Path:
        """Format the destination root folder."""
        return Path(self.constants.proposal_id)

    @property
    def output_frame_tags(self) -> list[str]:
        """Tags that uniquely identify L1 fits frames i.e. the dataset-inventory-able frames."""
        return [Tag.output(), Tag.frame()]

    @property
    def extra_frame_tags(self) -> list[str]:
        """Tags that uniquely identify dataset extra fits frames."""
        return [Tag.output(), Tag.extra()]


class TransferDataBase(OutputDataBase, ObjectStoreMixin, ABC):
    """Base class for transferring data from scratch to somewhere else."""

    def run(self) -> None:
        """Transfer the data and cleanup any folders."""
        with self.telemetry_span("Transfer objects"):
            self.transfer_objects()

        with self.telemetry_span("Remove folder objects"):
            self.remove_folder_objects()

    @abstractmethod
    def transfer_objects(self):
        """Collect objects and transfer them."""
        pass

    def build_output_frame_transfer_list(self) -> list[GlobusTransferItem]:
        """Build a list of GlobusTransfer items corresponding to all OUTPUT (i.e., L1) frames."""
        science_frame_paths: list[Path] = list(self.read(tags=self.output_frame_tags))

        return self.build_transfer_list(science_frame_paths)

    def build_dataset_extra_transfer_list(self) -> list[GlobusTransferItem]:
        """Build a list of GlobusTransfer items corresponding to all extra dataset files."""
        extra_paths: list[Path] = list(self.read(tags=self.extra_frame_tags))

        return self.build_transfer_list(paths=extra_paths, destination_folder_modifier="extra")

    def build_transfer_list(
        self, paths: list[Path], destination_folder_modifier: str | None = None
    ) -> list[GlobusTransferItem]:
        """Given a list of paths, build a list of GlobusTransfer items."""
        transfer_items = []
        for p in paths:
            object_key = self.format_object_key(path=p, folder_modifier=destination_folder_modifier)
            destination_path = Path(self.destination_bucket, object_key)
            item = GlobusTransferItem(
                source_path=p,
                destination_path=destination_path,
            )
            transfer_items.append(item)

        return transfer_items

    def remove_folder_objects(self):
        """Remove folder objects that would have been added by the Globus transfer."""
        removed_object_keys = self.object_store_remove_folder_objects(
            bucket=self.destination_bucket, path=self.destination_root_folder
        )
        logger.info(
            f"Removed folder objects in {self.destination_bucket} bucket. {removed_object_keys=}"
        )

    def rollback(self):
        """

        Rollback a Transfer Task.

        Globus transfers are not dependent upon the task once they are submitted.  Rolling back this task may not be achievable action on the destination.
        """
        super().rollback()
        logger.warning(f"Transferred objects may still exist at the destination.")
