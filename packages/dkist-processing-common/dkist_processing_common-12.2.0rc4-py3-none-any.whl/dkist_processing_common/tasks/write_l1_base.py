"""Base class for writing L1 FITS products with headers."""

import importlib
from abc import ABC
from functools import cached_property

import numpy as np
from astropy.io import fits

from dkist_processing_common.tasks import WorkflowTaskBase
from dkist_processing_common.tasks.mixin.metadata_store import MetadataStoreMixin


class WriteL1Base(WorkflowTaskBase, MetadataStoreMixin, ABC):
    """Base class for writing L1 FITS products with headers."""

    def version_from_module_name(self) -> str:
        """
        Get the value of __version__ from a module given its name.

        Returns
        -------
        The value of __version__
        """
        package = self.__module__.split(".")[0]
        module = importlib.import_module(package)
        return module.__version__

    @cached_property
    def workflow_had_manual_intervention(self) -> bool:
        """Indicate determining if any provenance capturing steps had manual intervention."""
        for provenance_record in self.metadata_store_recipe_run.recipeRunProvenances:
            if provenance_record.isTaskManual:
                return True
        return False

    def update_framevol(self, relative_path: str) -> None:
        """Update FRAMEVOL key to be exactly the size of the file on-disk."""
        full_path = self.scratch.workflow_base_path / relative_path
        compressed_size = full_path.stat().st_size / 1024 / 1024
        hdul = fits.open(full_path, mode="update")
        for i in range(1, len(hdul)):
            hdul[i].header["FRAMEVOL"] = compressed_size
        hdul.flush()
        del hdul

    @cached_property
    def tile_size_param(self) -> int | None:
        """Get the tile size parameter for compression."""
        return self.metadata_store_recipe_run.configuration.tile_size

    def compute_tile_size_for_array(self, data: np.ndarray) -> list | None:
        """Determine the tile size to use for compression accounting for array shape minimums."""
        if self.tile_size_param is None:
            return None
        tile_size = []
        for dim_size in data.shape:
            if dim_size < self.tile_size_param:
                tile_size.append(dim_size)
            else:
                tile_size.append(self.tile_size_param)
        return tile_size

    @cached_property
    def validate_l1_on_write(self) -> bool:
        """Check for validate on write."""
        return self.metadata_store_recipe_run.configuration.validate_l1_on_write
