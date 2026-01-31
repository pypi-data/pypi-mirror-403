"""Autocomplete access to dataset extra header sections."""

from enum import StrEnum


class DatasetExtraHeaderSection(StrEnum):
    """Enum defining the possible header sections for dataset extras."""

    common = "common"
    aggregate = "aggregate"
    iptask = "iptask"
    gos = "gos"
    wavecal = "wavecal"
    atlas = "atlas"
    test = "test"


class DatasetExtraType(StrEnum):
    """Enum defining options for dataset extra names."""

    dark = "DARK"
    background_light = "BACKGROUND LIGHT"
    solar_gain = "SOLAR GAIN"
    characteristic_spectra = "CHARACTERISTIC SPECTRA"
    modulation_state_offsets = "MODULATION STATE OFFSETS"
    beam_angles = "BEAM ANGLES"
    spectral_curvature_shifts = "SPECTRAL CURVATURE SHIFTS"
    wavelength_calibration_input_spectrum = "WAVELENGTH CALIBRATION INPUT SPECTRUM"
    wavelength_calibration_reference_spectrum = "WAVELENGTH CALIBRATION REFERENCE SPECTRUM"
    reference_wavelength_vector = "REFERENCE WAVELENGTH VECTOR"
    demodulation_matrices = "DEMODULATION MATRICES"
    polcal_as_science = "POLCAL AS SCIENCE"
    bad_pixel_map = "BAD PIXEL MAP"
    beam_offsets = "BEAM OFFSETS"
    spectral_curvature_scales = "SPECTRAL CURVATURE SCALES"
