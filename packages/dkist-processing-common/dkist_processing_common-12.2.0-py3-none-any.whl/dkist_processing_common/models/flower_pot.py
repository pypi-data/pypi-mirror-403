"""
Framework for grouping multiple keys and values with arbitrary logic.

The key components are:
    **Stem:** ABC for groupings that depend on both the key and (maybe) value. Subgroups (Petals) are implied but not enforced.

    **ListStem:** ABC for groups that depend on value only. More limited, but faster than `Stem` for cases where the keys don't matter.

    **SetStem:** ABC for groups that depend on value only and the values are well represented by a `set`. Even more limited, but faster than `Stem` for cases where the keys don't matter.

    **FlowerPot:** Container for Stem children (Flowers)
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Hashable
from typing import Any


class FlowerPot:
    """Base class to hold multiple sets (Stems) of key, value pairs."""

    def __init__(self):
        self.stems: list[Stem] = list()

    def __iter__(self):
        return self.stems.__iter__()

    def __len__(self):
        return self.stems.__len__()

    def __getitem__(self, item):
        return self.stems.__getitem__(item)

    def add_dirt(self, key: Hashable, value: Any) -> None:
        """
        Send key and value through all Stems.

        Parameters
        ----------
        key
            The key
        value
            The value

        Returns
        -------
        None
        """
        if not isinstance(key, Hashable):
            raise TypeError(f"Type of key ({type(key)}) is not hashable")

        for stem in self.stems:
            stem.update(key, value)


class SpilledDirt:
    """
    A custom class for when a Stem wants the FlowerPot to skip that particular key/value.

    Exists because None, False, [], (), etc. etc. are all valid Stem return values
    """


class Thorn:
    """
    Custom class to indicate that a Bud's value should not be used.

    I.e., don't pick this Bud because it's thorny. This exists for "Picky" Buds that merely perform a check and Error
    on failure. If the check passes we don't need to do anything with the Bud's value and that value should be a Thorn.
    """


class Petal:
    """
    Base class to hold a single key, value pair.

    Parameters
    ----------
    item
        The key, value pair to be added
    """

    def __init__(self, item: tuple):
        self.value = item[0]
        self.keys = item[1]

    def __repr__(self):
        return f"Petal: {{{self.value}: {self.keys}}}"


class Stem(ABC):
    """
    Base class for grouping keys via arbitrary logic on the total collection of keys and values.

    Parameters
    ----------
    stem_name
        The name to be associated with the stem
    """

    def __init__(self, stem_name: Any):
        self.stem_name = stem_name
        self.key_to_petal_dict: dict[Hashable, Hashable] = dict()

        self._petal_cache: list[Petal] = []
        self._need_to_generate_petals: bool = True

    def update(self, key: Hashable, value: Any) -> None:
        """
        Ingest a single key/value pair.

        Parameters
        ----------
        key
            The key
        value
            The value

        Returns
        -------
        None
        """
        result = self.setter(value)
        if result is not SpilledDirt:
            self.key_to_petal_dict[key] = result
            self._need_to_generate_petals = True

    @property
    def petals(self) -> list[Petal]:
        """Return subgroups and associated keys."""
        if self._need_to_generate_petals:
            self._generate_petal_list()

        return self._petal_cache

    @property
    def can_be_picked(self) -> bool:
        """
        Return True if there are any values to be picked.

        A `Stem` could have no values even after dirt is added if all of the results were `SpilledDirt`.
        """
        return len(self.petals) > 0

    def _generate_petal_list(self) -> None:
        """
        Generate a list of petals.

        Generating a petal list can be expensive because it involves inverting the `key_to_petal_dict`. To avoid doing
        this every the `petals` property is accessed, this method produces a cached list of petals that is only
        re-generated when the `key_to_petal_dict` has been updated.

        Note: We can't make `petals` a `@cached_property` because that would make `petals` always tied to whatever the
        state of this `Stem` was when `petals` was first accessed. And we can't use `lru_cache` because the object that
        changes, `key_to_petal_dict`, is unhashable.
        """
        petal_to_key_dict = defaultdict(list)
        for key in self.key_to_petal_dict.keys():
            petal = self.getter(key)
            petal_to_key_dict[petal].append(key)

        self._petal_cache = [Petal(item) for item in petal_to_key_dict.items()]
        self._need_to_generate_petals = False

    @property
    def bud(self) -> Petal:
        """Just the first petal."""
        bud = self.petals[0]
        return bud

    @abstractmethod
    def setter(self, value: Any) -> Any:
        """
        Logic to apply to a single key/value pair on ingest.

        Implemented in derived class.

        Parameters
        ----------
        value
            The value to be added

        Returns
        -------
        Any
        """
        pass

    @abstractmethod
    def getter(self, key: Hashable) -> Hashable:
        """
        Logic to apply to all ingested values when picking the Stem.

        Implemented in derived class.

        Parameters
        ----------
        key
            The key to return the value of
        Returns
        -------
        The value
        """
        pass


class ListStem(ABC):
    """
    Base class for collecting and applying logic to values in a `list` with a `Stem`-like interface.

    Unlike the full `Stem`, this class does NOT retain information about the keys and thus does no grouping of keys based
    on values. The direct consequence of this is that the `.petals` property is undefined and will raise an ``AttributeError``
    if accessed. This also means there is no need to invert the `key_to_petal_dict` (because it doesn't exist), which,
    in turn, means there is no need to run the `getter` for every key. The result is that the `bud` property only needs
    one call to `getter`. Thus, the calculation of a single value derived from all values (i.e., `bud`) is much faster
    than using a full `Stem`.

    Parameters
    ----------
    stem_name
        The name to be associated with the stem
    """

    def __init__(self, stem_name: Any):
        self.stem_name = stem_name
        self.value_list: list = list()
        self._need_to_compute_bud_value: bool = True

    def update(self, key: Any, value: Any) -> None:
        """
        Ingest a single key/value pair. Note that the ``key`` is not used.

        Parameters
        ----------
        key
            The key (unused)

        value
            The value

        Returns
        -------
        None
        """
        result = self.setter(value)
        if result is not SpilledDirt:
            self.value_list.append(result)
            self._need_to_compute_bud_value = True

    @property
    def petals(self) -> None:
        """Raise an error because `ListStem` does not retain key information and therefore cannot group keys."""
        raise AttributeError(
            f"{self.__class__.__name__} subclasses ListStem and therefore does not define the `petals` property"
        )

    @property
    def can_be_picked(self) -> bool:
        """
        Return True if there are any values to be picked.

        A `Stem` could have no values even after dirt is added if all of the results were `SpilledDirt`.
        """
        return len(self.value_list) > 0

    @property
    def bud(self) -> Petal:
        """Return the result of `getter` packaged in a `Petal` object."""
        if self._need_to_compute_bud_value:
            self._value_cache = self.getter()
            self._need_to_compute_bud_value = False

        return Petal((self._value_cache, "LISTSTEM_NOT_USED"))

    @abstractmethod
    def setter(self, value: Any) -> Any:
        """
        Logic to apply to a single value pair on ingest.

        Implemented in derived class.

        Parameters
        ----------
        value
            The value to be added

        Returns
        -------
        Any
        """
        pass

    @abstractmethod
    def getter(self) -> Any:
        """
        Logic to apply to all ingested values when computing the `bud`.

        Implemented in derived class.

        Returns
        -------
        The value of the bud
        """
        pass


class SetStem(ABC):
    """
    Base class for collecting and applying logic to values in a `set` with a `Stem`-like interface.

    Unlike the full `Stem`, this class does NOT retain information about the keys and thus does no grouping of keys based
    on values. The direct consequence of this is that the `.petals` property is undefined and will raise an ``AttributeError``
    if accessed. This also means there is no need to invert the `key_to_petal_dict` (because it doesn't exist), which,
    in turn, means there is no need to run the `getter` for every key. The result is that the `bud` property only needs
    one call to `getter`. Combined with the efficiency of storing values in a `set`, the calculation of a single value
    derived from all values (i.e., `bud`) is much faster than using a full `Stem`.

    .. Note::
      The use of a `set` as the underlying storage mechanism means information regarding how many times a particular value
      is present will be lost. It also means the return type of `setter` must be hashable. Both of these constraints can
      be avoided by using `ListStem`, which still gets a significant speedup over `Stem` by dropping key information.


    Parameters
    ----------
    stem_name
        The name to be associated with the stem
    """

    def __init__(self, stem_name: Any):
        self.stem_name = stem_name
        self.value_set: set = set()
        self._need_to_compute_bud_value: bool = True

    def update(self, key: Any, value: Any) -> None:
        """
        Ingest a single key/value pair. Note that the ``key`` is not used.

        Parameters
        ----------
        key
            The key (unused)

        value
            The value

        Returns
        -------
        None
        """
        result = self.setter(value)
        if result is not SpilledDirt:
            self.value_set.add(result)
            self._need_to_compute_bud_value = True

    @property
    def petals(self) -> None:
        """Raise an error because `SetStem` does not retain key information and therefore cannot group keys."""
        raise AttributeError(
            f"{self.__class__.__name__} subclasses SetStem and therefore does not define the `petals` property"
        )

    @property
    def can_be_picked(self) -> bool:
        """
        Return True if there are any values to be picked.

        A `Stem` could have no values even after dirt is added if all of the results were `SpilledDirt`.
        """
        return len(self.value_set) > 0

    @property
    def bud(self) -> Petal:
        """Return the result of `getter` packaged in a `Petal` object."""
        if self._need_to_compute_bud_value:
            self._value_cache = self.getter()
            self._need_to_compute_bud_value = False

        return Petal((self._value_cache, "SETSTEM_NOT_USED"))

    @abstractmethod
    def setter(self, value: Any) -> Hashable:
        """
        Logic to apply to a single value pair on ingest.

        Must return a Hashable object because the result will be stored in a `set`.

        Implemented in derived class.

        Parameters
        ----------
        value
            The value to be added

        Returns
        -------
        Any
        """
        pass

    @abstractmethod
    def getter(self) -> Any:
        """
        Logic to apply to all ingested values when computing the `bud`.

        Implemented in derived class.

        Returns
        -------
        The value of the bud
        """
        pass
