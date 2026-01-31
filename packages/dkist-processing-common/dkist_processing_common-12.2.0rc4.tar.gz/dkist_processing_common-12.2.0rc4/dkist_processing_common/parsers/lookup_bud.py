"""Simple bud that is used to set a constant to a mapping dictionary."""

from collections import defaultdict
from enum import StrEnum
from typing import Any
from typing import Callable
from typing import DefaultDict

from dkist_processing_common.models.flower_pot import SetStem
from dkist_processing_common.models.flower_pot import SpilledDirt
from dkist_processing_common.models.tags import EXP_TIME_ROUND_DIGITS
from dkist_processing_common.parsers.l0_fits_access import L0FitsAccess
from dkist_processing_common.parsers.task import passthrough_header_ip_task


class TimeLookupBud(SetStem):
    """
    Bud that reads two header keys from all files and creates a dictionary mapping a time KEY value to sets of a VALUE value.

    Parameters
    ----------
    constant_name
        The name for the constant to be defined

    key_metadata_key
        The time metadata key for the resulting dictionary key

    value_metadata_key
        The metadata key for the resulting dictionary value
    """

    def __init__(
        self,
        constant_name: str,
        key_metadata_key: str | StrEnum,
        value_metadata_key: str | StrEnum,
    ):
        super().__init__(stem_name=constant_name)

        if isinstance(key_metadata_key, StrEnum):
            key_metadata_key = key_metadata_key.name
        self.key_metadata_key = key_metadata_key
        if isinstance(value_metadata_key, StrEnum):
            value_metadata_key = value_metadata_key.name
        self.value_metadata_key = value_metadata_key

        self.mapping: DefaultDict[float, set[Any]] = defaultdict(set)

    def setter(self, fits_obj: L0FitsAccess):
        """
        Update the mapping dictionary.

        Parameters
        ----------
        fits_obj
            The input fits object
        Returns
        -------
        Updates the dictionary and returns None
        """
        key = getattr(fits_obj, self.key_metadata_key)
        rounded_key = round(key, EXP_TIME_ROUND_DIGITS)
        value = getattr(fits_obj, self.value_metadata_key)
        self.mapping[rounded_key].add(value)
        return None

    def getter(self):
        """
        Get the dictionary mapping created by the setter with values converted to JSON-able lists.

        Returns
        -------
        The mapping dictionary with values converted to JSON-able lists
        """
        mapping_lists = {k: list(v) for k, v in self.mapping.items()}
        return mapping_lists


class TaskTimeLookupBud(TimeLookupBud):
    """
    Subclass of `TimeLookupBud` that only considers objects that have specific task types.

    Parameters
    ----------
    constant_name
        The name for the constant to be defined

    key_metadata_key
        The time metadata key for the resulting dictionary key

    value_metadata_key
        The metadata key for the resulting dictionary value

    ip_task_types
        Only consider objects whose parsed header IP task type matches a string in this list

    task_type_parsing_function
        The function used to convert a header into an IP task type
    """

    def __init__(
        self,
        constant_name: str,
        key_metadata_key: str | StrEnum,
        value_metadata_key: str | StrEnum,
        ip_task_types: str | list[str],
        task_type_parsing_function: Callable = passthrough_header_ip_task,
    ):
        super().__init__(
            constant_name=constant_name,
            key_metadata_key=key_metadata_key,
            value_metadata_key=value_metadata_key,
        )
        if isinstance(ip_task_types, str):
            ip_task_types = [ip_task_types]
        self.ip_task_types = [task.casefold() for task in ip_task_types]
        self.parsing_function = task_type_parsing_function

    def setter(self, fits_obj: L0FitsAccess):
        """Ingest an object only if its parsed IP task type matches what's desired."""
        task = self.parsing_function(fits_obj)
        if task.casefold() in self.ip_task_types:
            return super().setter(fits_obj)

        return SpilledDirt
