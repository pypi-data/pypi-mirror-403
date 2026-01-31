"""Bud that parses the name of the retarder used during POLCAL task observations."""

from dkist_processing_common.models.constants import BudName
from dkist_processing_common.models.fits_access import MetadataKey
from dkist_processing_common.models.flower_pot import SpilledDirt
from dkist_processing_common.models.task_name import TaskName
from dkist_processing_common.parsers.l0_fits_access import L0FitsAccess
from dkist_processing_common.parsers.unique_bud import TaskUniqueBud


class RetarderNameBud(TaskUniqueBud):
    """
    Bud for determining the name of the retarder used during a polcal Calibration Sequence (CS).

    This is *slightly* different than a simple `TaskUniqueBud` because we need to allow for CS steps when the retarder
    is out of the beam (i.g., "clear"). We do this by returning `SpilledDirt` from the `setter` if the value is "clear".
    """

    def __init__(self):
        super().__init__(
            constant_name=BudName.retarder_name,
            metadata_key=MetadataKey.gos_retarder_status,
            ip_task_types=TaskName.polcal,
        )

    def setter(self, fits_obj: L0FitsAccess) -> type[SpilledDirt] | str:
        """Drop the result if the retarder is out of the beam ("clear")."""
        result = super().setter(fits_obj)
        if result is not SpilledDirt and result.casefold() == "clear":
            return SpilledDirt

        return result
