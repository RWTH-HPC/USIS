"""
Tests whether properties about the collection of KINDs in bindinytypes.py.
"""


# pylint: disable=import-error, redefined-outer-name


import logging
from pprint import pformat
from typing import Mapping, List
import pytest


import bindingtypes


@pytest.fixture
def maps() -> List[Mapping[str, str]]:
    """
    Load all KIND mappings into a list.
    """

    return [
        bindingtypes.LIS_KIND_MAP,

        bindingtypes.BASE_C_KIND_MAP,
        bindingtypes.SMALL_C_KIND_MAP,
        bindingtypes.BIG_C_KIND_MAP,

        bindingtypes.BASE_F90_KIND_MAP,
        bindingtypes.SMALL_F90_KIND_MAP,
        bindingtypes.BIG_F90_KIND_MAP,

        bindingtypes.BASE_F08_KIND_MAP,
        bindingtypes.SMALL_F08_KIND_MAP,
        bindingtypes.BIG_F08_KIND_MAP,
        bindingtypes.OR_F08_KIND_MAP,
        ]


def test_all_kinds_in_all_languages(maps):
    """
    Verify that all individual KINDs are in all language mappings.
    """

    for kind in bindingtypes.LIS_KIND_MAP.keys():
        for mapping in maps:
            assert kind in mapping


def test_all_poly_have_big_and_small(maps):
    """
    Tests whether all POLY KINDs have a '*' KIND as well.
    """

    for mapping in maps:
        for kind in mapping.keys():
            if kind.startswith('POLY'):
                small_name = f"{kind.replace('POLY', '')}_SMALL"
                assert small_name in mapping

                big_name = f"{kind.replace('POLY', '')}"
                assert big_name in mapping


def test_small_big_maps_to_small_big_kinds():
    """
    Tests whether the POLY KIND _SMALL and * are the same in the
    SMALL and BIG mapping of that KIND.
    """

    maps_small = [
        bindingtypes.SMALL_C_KIND_MAP,
        bindingtypes.SMALL_F08_KIND_MAP,
        bindingtypes.SMALL_F90_KIND_MAP,
        ]

    maps_big = [
        bindingtypes.BIG_C_KIND_MAP,
        bindingtypes.BIG_F08_KIND_MAP,
        bindingtypes.BIG_F90_KIND_MAP,
        ]

    for kind in bindingtypes.LIS_KIND_MAP.keys():
        if kind.startswith('POLY'):
            small_name = f"{kind.replace('POLY', '')}_SMALL"
            big_name = f"{kind.replace('POLY', '')}"

            for mapping in maps_small:
                assert mapping[kind] == mapping[small_name], kind

            for mapping in maps_big:
                assert mapping[kind] == mapping[big_name], kind


def test_kinds_with_lis_variants_are_equal():
    """
    Tests whether any KIND which has LIS variants (_NNI, _PI) are
    different in the actual languages (C, F08, F90).

    RMA_DISPLACEMENT_SMALL
    RMA_DISPLACEMENT
    POLYRMA_DISPLACEMENT

    RMA_DISPLACEMENT_NNI_SMALL
    RMA_DISPLACEMENT_NNI
    POLYRMA_DISPLACEMENT_NNI
    """

    maps = [
        bindingtypes.SMALL_C_KIND_MAP,
        bindingtypes.SMALL_F08_KIND_MAP,
        bindingtypes.SMALL_F90_KIND_MAP,
        bindingtypes.BIG_C_KIND_MAP,
        bindingtypes.BIG_F08_KIND_MAP,
        bindingtypes.BIG_F90_KIND_MAP,
        ]

    for kind in bindingtypes.LIS_KIND_MAP.keys():
        if '_NNI' in kind or '_PI' in kind:
            name = kind.replace('_NNI', '').replace('_PI', '')

            for mapping in maps:
                assert mapping[name] == mapping[kind]


def test_poly_kind_lis_matches():
    """
    Tests whether a POLYKIND LIS matches the KIND and KIND_SMALL.
    """

    mapping = bindingtypes.LIS_KIND_MAP

    for kind, lis in mapping.items():
        if kind.startswith('POLY'):
            small_name = f"{kind.replace('POLY', '')}_SMALL"
            big_name = f"{kind.replace('POLY', '')}"

            assert mapping[small_name] == lis, kind
            assert mapping[big_name] == lis, kind
