from typing import Any
from typing import Hashable

import pytest

from dkist_processing_common.models.flower_pot import FlowerPot
from dkist_processing_common.models.flower_pot import ListStem
from dkist_processing_common.models.flower_pot import SetStem
from dkist_processing_common.models.flower_pot import SpilledDirt
from dkist_processing_common.models.flower_pot import Stem


@pytest.fixture
def simple_flower():
    class Flower(Stem):
        def setter(self, value: Any) -> Any:
            if value < 0:
                return SpilledDirt
            return value % 2

        def getter(self, key: Hashable) -> Hashable:
            return self.key_to_petal_dict[key]

    return Flower(stem_name="simple_flower")


@pytest.fixture
def simple_flower_pot(simple_flower):
    flower_pot = FlowerPot()
    flower_pot.stems += [simple_flower]

    return flower_pot


@pytest.fixture
def simple_key_values():
    return {f"thing{i}": i for i in range(5)}


@pytest.fixture
def stem_bud():
    class Bud(Stem):
        def setter(self, value: int) -> int:
            return value % 3

        def getter(self, key: str) -> int:
            return len(set(self.key_to_petal_dict.values()))

    return Bud(stem_name="StemBud")


@pytest.fixture
def setstem_bud():
    # Computes the same result as `stem_bud`
    class SetBud(SetStem):
        def setter(self, value: int) -> int:
            return value % 3

        def getter(self) -> int:
            return len(self.value_set)

    return SetBud(stem_name="SetStemBud")


@pytest.fixture
def liststem_bud():
    # Highlights the difference between using a `set` and a `list` in these more efficient buds
    class ListBud(ListStem):
        def setter(self, value: int) -> int:
            return value % 3

        def getter(self) -> int:
            return len(self.value_list)

    return ListBud(stem_name="ListStemBud")


@pytest.fixture
def simple_bud_pot(stem_bud, setstem_bud, liststem_bud):
    bud_pot = FlowerPot()
    bud_pot.stems += [stem_bud, liststem_bud, setstem_bud]
    return bud_pot


@pytest.fixture
def bud_key_values():
    return {f"DOESN'T_MATTER_THAT'S_THE_POINT_{i}": i for i in [0, 1, 3, 4]}


def test_simple_flower_pot(simple_flower_pot, simple_key_values):
    """
    Given: A FlowerPot with a simple Flower
    When: Updating flower with key: value pairs
    Then: The flower are correctly updated
    """
    assert len(simple_flower_pot) == 1

    flower = simple_flower_pot[0]
    assert flower.stem_name == "simple_flower"

    for k, m in simple_key_values.items():
        simple_flower_pot.add_dirt(k, m)

    petals = sorted(list(flower.petals), key=lambda x: x.value)
    assert len(petals) == 2
    assert flower.bud.value == petals[0].value
    assert flower.bud.keys == petals[0].keys
    assert petals[0].value == 0
    assert petals[0].keys == ["thing0", "thing2", "thing4"]
    assert petals[1].value == 1
    assert petals[1].keys == ["thing1", "thing3"]


def test_cached_petal(simple_flower):
    """
    Given: A Stem object
    When: Ingesting a (key, value) pair with `.update` *after* examining the `petals` property
    Then: The `petals` property still gets updated with the new (key, value) pair
    """
    key1 = "thing1"
    value1 = 4
    simple_flower.update(key1, value1)
    assert len(simple_flower.petals) == 1

    # Assert twice to hit the cache
    assert simple_flower.petals[0].value == value1 % 2  # % 2 because of simple_flower's `setter`
    assert simple_flower.petals[0].keys == [key1]
    assert simple_flower.petals[0].value == value1 % 2
    assert simple_flower.petals[0].keys == [key1]

    key2 = "thing2"
    value2 = 3
    simple_flower.update(key2, value2)
    assert len(simple_flower.petals) == 2
    sorted_petals = sorted(simple_flower.petals, key=lambda x: x.value)
    assert sorted_petals[0].value == value1 % 2
    assert sorted_petals[0].keys == [key1]
    assert sorted_petals[1].value == value2 % 2
    assert sorted_petals[1].keys == [key2]
    assert sorted_petals[0].value == value1 % 2
    assert sorted_petals[0].keys == [key1]
    assert sorted_petals[1].value == value2 % 2
    assert sorted_petals[1].keys == [key2]


def test_spilled_dirt_flower(simple_flower):
    """
    Given: A simple Flower with logic to deal with SpilledDirt
    When: Updating the flower with a key/value that causes dirt to be spilled
    Then: The Flower ignores the input key/value
    """
    key = "thing0"
    value = -1
    simple_flower.update(key, value)
    assert len(list(simple_flower.petals)) == 0


def test_unhashable_dirt(simple_flower_pot):
    """
    Given: A FlowerPot
    When: Adding dirt with a key that is not hashable
    Then: An Error is raised
    """
    unhashable_key = ["a", "list"]
    value = "never gonna get here"
    with pytest.raises(TypeError):
        simple_flower_pot.add_dirt(unhashable_key, value)


def test_buds(simple_bud_pot, bud_key_values):
    """
    Given: A Flower pot with two Buds that compute the same thing; one a `Stem` and one a `SetStem`, and a `ListStem` bud
    When: Updating the pot with key: value pairs
    Then: The computed buds are correct and the `Stem` and `SetStem` buds match
    """
    assert len(simple_bud_pot) == 3

    assert simple_bud_pot[0].stem_name == "StemBud"
    assert simple_bud_pot[1].stem_name == "ListStemBud"
    assert simple_bud_pot[2].stem_name == "SetStemBud"

    for k, m in bud_key_values.items():
        simple_bud_pot.add_dirt(k, m)

    assert simple_bud_pot[0].bud.value == 2
    assert simple_bud_pot[1].bud.value == 4
    assert simple_bud_pot[2].bud.value == simple_bud_pot[0].bud.value

    assert len(simple_bud_pot[0].petals) == 1
    assert simple_bud_pot[0].petals[0].value == 2
    assert simple_bud_pot[0].petals[0].keys == [
        f"DOESN'T_MATTER_THAT'S_THE_POINT_{i}" for i in [0, 1, 3, 4]
    ]

    with pytest.raises(
        AttributeError,
        match="ListBud subclasses ListStem and therefore does not define the `petals` property",
    ):
        _ = simple_bud_pot[1].petals

    with pytest.raises(
        AttributeError,
        match="SetBud subclasses SetStem and therefore does not define the `petals` property",
    ):
        _ = simple_bud_pot[2].petals


def test_liststem_cached_bud(liststem_bud):
    """
    Given: A `ListStem` instance and some different input values
    When: Computing the `bud` property after each value is ingested
    Then: The `bud` value correctly updates based on the state of the `ListStem` object
    """
    key = "Who cares"
    value1 = 3
    liststem_bud.update(key, value1)

    # Assert twice so we hit the cache
    assert liststem_bud.bud.value == 1
    assert liststem_bud.bud.value == 1

    value2 = 1
    liststem_bud.update(key, value2)

    assert liststem_bud.bud.value == 2
    assert liststem_bud.bud.value == 2


def test_setstem_cached_bud(setstem_bud):
    """
    Given: A `SetStem` instance and some different input values
    When: Computing the `bud` property after each value is ingested
    Then: The `bud` value correctly updates based on the state of the `SetStem` object
    """
    key = "Who cares"
    value1 = 3
    setstem_bud.update(key, value1)

    # Assert twice so we hit the cache
    assert setstem_bud.bud.value == 1
    assert setstem_bud.bud.value == 1

    value2 = 1
    setstem_bud.update(key, value2)

    assert setstem_bud.bud.value == 2
    assert setstem_bud.bud.value == 2
