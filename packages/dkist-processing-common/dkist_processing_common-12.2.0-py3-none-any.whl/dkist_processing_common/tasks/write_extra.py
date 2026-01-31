"""Classes to support the generation of dataset extras."""

import uuid
from abc import ABC
from abc import abstractmethod
from datetime import datetime

import numpy as np
from astropy.io import fits
from astropy.time import Time
from dkist_fits_specifications.utils.formatter import reformat_dataset_extra_header
from dkist_header_validator.spec_validators import spec_extras_validator

from dkist_processing_common.codecs.fits import fits_hdulist_encoder
from dkist_processing_common.models.extras import DatasetExtraHeaderSection
from dkist_processing_common.models.extras import DatasetExtraType
from dkist_processing_common.models.tags import Tag
from dkist_processing_common.models.task_name import TaskName
from dkist_processing_common.tasks.write_l1_base import WriteL1Base


class WriteL1DatasetExtras(WriteL1Base, ABC):
    """Class supporting the construction of dataset extras."""

    def dataset_extra_headers(
        self,
        filename: str,
        task_type: TaskName,
        extra_name: DatasetExtraType,
        end_time: str,
        total_exposure: float | None = None,
        readout_exposure: float | None = None,
    ) -> dict:
        """Provide common FITS header keys for dataset extras."""
        # Build task specific header values
        match task_type:
            case TaskName.dark:
                task_specific_observing_program_execution_id = (
                    self.constants.dark_observing_program_execution_ids
                )
                task_specific_date_begin = self.constants.dark_date_begin
                task_specific_raw_frames_per_fpa = (
                    0  # can be updated in construction of dataset extra if required
                )
                task_specific_telescope_tracking_mode = (
                    "None"  # can be updated in construction of dataset extra if required
                )
                task_specific_coude_table_tracking_mode = (
                    "None"  # can be updated in construction of dataset extra if required
                )
                task_specific_telescope_scanning_mode = (
                    "None"  # can be updated in construction of dataset extra if required
                )
                task_specific_average_light_level = self.constants.dark_average_light_level
                task_specific_average_telescope_elevation = (
                    self.constants.dark_average_telescope_elevation
                )
                task_specific_average_coude_table_angle = (
                    self.constants.dark_average_coude_table_angle
                )
                task_specific_average_telescope_azimuth = (
                    self.constants.dark_average_telescope_azimuth
                )
                task_specific_gos_level3_status = self.constants.dark_gos_level3_status
                task_specific_gos_level3_lamp_status = self.constants.dark_gos_level3_lamp_status
                task_specific_gos_polarizer_status = self.constants.dark_gos_polarizer_status
                task_specific_gos_polarizer_angle = self.constants.dark_gos_polarizer_angle
                task_specific_gos_retarder_status = self.constants.dark_gos_retarder_status
                task_specific_gos_retarder_angle = self.constants.dark_gos_retarder_angle
                task_specific_gos_level0_status = self.constants.dark_gos_level0_status
            case TaskName.solar_gain:
                task_specific_observing_program_execution_id = (
                    self.constants.solar_gain_observing_program_execution_ids
                )

                task_specific_date_begin = self.constants.solar_gain_date_begin
                task_specific_raw_frames_per_fpa = self.constants.solar_gain_num_raw_frames_per_fpa
                task_specific_telescope_tracking_mode = (
                    self.constants.solar_gain_telescope_tracking_mode
                )
                task_specific_coude_table_tracking_mode = (
                    self.constants.solar_gain_coude_table_tracking_mode
                )
                task_specific_telescope_scanning_mode = (
                    self.constants.solar_gain_telescope_scanning_mode
                )
                task_specific_average_light_level = self.constants.solar_gain_average_light_level
                task_specific_average_telescope_elevation = (
                    self.constants.solar_gain_average_telescope_elevation
                )
                task_specific_average_coude_table_angle = (
                    self.constants.solar_gain_average_coude_table_angle
                )
                task_specific_average_telescope_azimuth = (
                    self.constants.solar_gain_average_telescope_azimuth
                )
                task_specific_gos_level3_status = self.constants.solar_gain_gos_level3_status
                task_specific_gos_level3_lamp_status = (
                    self.constants.solar_gain_gos_level3_lamp_status
                )
                task_specific_gos_polarizer_status = self.constants.solar_gain_gos_polarizer_status
                task_specific_gos_polarizer_angle = self.constants.solar_gain_gos_polarizer_angle
                task_specific_gos_retarder_status = self.constants.solar_gain_gos_retarder_status
                task_specific_gos_retarder_angle = self.constants.solar_gain_gos_retarder_angle
                task_specific_gos_level0_status = self.constants.solar_gain_gos_level0_status
            case TaskName.polcal:
                task_specific_observing_program_execution_id = (
                    self.constants.polcal_observing_program_execution_ids
                )

                task_specific_date_begin = self.constants.polcal_date_begin
                task_specific_raw_frames_per_fpa = self.constants.polcal_num_raw_frames_per_fpa
                task_specific_telescope_tracking_mode = (
                    self.constants.polcal_telescope_tracking_mode
                )
                task_specific_coude_table_tracking_mode = (
                    self.constants.polcal_coude_table_tracking_mode
                )
                task_specific_telescope_scanning_mode = (
                    self.constants.polcal_telescope_scanning_mode
                )
                task_specific_average_light_level = self.constants.polcal_average_light_level
                task_specific_average_telescope_elevation = (
                    self.constants.polcal_average_telescope_elevation
                )
                task_specific_average_coude_table_angle = (
                    self.constants.polcal_average_coude_table_angle
                )
                task_specific_average_telescope_azimuth = (
                    self.constants.polcal_average_telescope_azimuth
                )
                task_specific_gos_level3_status = None
                task_specific_gos_level3_lamp_status = None
                task_specific_gos_polarizer_status = None
                task_specific_gos_polarizer_angle = None
                task_specific_gos_retarder_status = None
                task_specific_gos_retarder_angle = None
                task_specific_gos_level0_status = None
            case _:
                raise ValueError(f"Unsupported task type {task_type}")

        start_datetime = datetime.fromisoformat(task_specific_date_begin)
        end_datetime = datetime.fromisoformat(end_time)

        dataset_extra_header = {
            DatasetExtraHeaderSection.common: {
                "BUNIT": "count",
                "DATE": Time.now().fits,
                "DATE-BEG": task_specific_date_begin,
                "DATE-END": end_time,
                "TELAPSE": (end_datetime - start_datetime).total_seconds(),
                "DATE-AVG": (start_datetime + (end_datetime - start_datetime) / 2).isoformat(),
                "TIMESYS": "UTC",
                "ORIGIN": "National Solar Observatory",
                "TELESCOP": "Daniel K. Inouye Solar Telescope",
                "OBSRVTRY": "Haleakala High Altitude Observatory Site",
                "NETWORK": "NSF-DKIST",
                "INSTRUME": self.constants.instrument,
                "OBJECT": "unknown",
                "CAM_ID": self.constants.camera_id,
                "CAMERA": self.constants.camera_name,
                "BITDEPTH": self.constants.camera_bit_depth,
                "XPOSURE": total_exposure,
                "TEXPOSUR": readout_exposure,
                "HWBIN1": self.constants.hardware_binning_x,
                "HWBIN2": self.constants.hardware_binning_y,
                "SWBIN1": self.constants.software_binning_x,
                "SWBIN2": self.constants.software_binning_y,
                "NSUMEXP": task_specific_raw_frames_per_fpa,
                "DSETID": self.constants.dataset_id,
                "PROCTYPE": "L1_EXTRA",
                "RRUNID": self.recipe_run_id,
                "RECIPEID": self.metadata_store_recipe_run.recipeInstance.recipeId,
                "RINSTID": self.metadata_store_recipe_run.recipeInstanceId,
                "FILENAME": filename,
                "HEAD_URL": "",
                "INFO_URL": self.docs_base_url,
                "CAL_URL": "",
                "CALVERS": self.version_from_module_name(),
                "IDSPARID": (
                    parameters.inputDatasetPartId
                    if (parameters := self.metadata_store_input_dataset_parameters)
                    else None
                ),
                "IDSOBSID": (
                    observe_frames.inputDatasetPartId
                    if (observe_frames := self.metadata_store_input_dataset_observe_frames)
                    else None
                ),
                "IDSCALID": (
                    calibration_frames.inputDatasetPartId
                    if (calibration_frames := self.metadata_store_input_dataset_calibration_frames)
                    else None
                ),
                "WKFLVERS": self.workflow_version,
                "WKFLNAME": self.workflow_name,
                "MANPROCD": self.workflow_had_manual_intervention,
                "FILE_ID": uuid.uuid4().hex,
                "OBSPR_ID": task_specific_observing_program_execution_id[
                    0
                ],  # The OP IDs are stored sorted by number of appearances of each OP ID in the source task type frames
                "EXTOBSID": ",".join(task_specific_observing_program_execution_id[1:]),
                "EXPER_ID": self.constants.experiment_id,
                "PROP_ID": self.constants.proposal_id,
                "HLSVERS": self.constants.hls_version,
                "LINEWAV": self.constants.wavelength,
                "TELTRACK": (
                    task_specific_telescope_tracking_mode if task_type != TaskName.dark else None
                ),
                "TTBLTRCK": (
                    task_specific_coude_table_tracking_mode if task_type != TaskName.dark else None
                ),
                "TELSCAN": (
                    task_specific_telescope_scanning_mode if task_type != TaskName.dark else None
                ),
                "EXTNAME": extra_name,
            },
            DatasetExtraHeaderSection.aggregate: {
                "AVGLLVL": task_specific_average_light_level,
                "ATELEVAT": task_specific_average_telescope_elevation,
                "ATTBLANG": task_specific_average_coude_table_angle,
                "ATAZIMUT": task_specific_average_telescope_azimuth,
            },
            DatasetExtraHeaderSection.iptask: {
                "IPTASK": "GAIN" if "GAIN" in task_type else task_type,
            },
            DatasetExtraHeaderSection.gos: {
                "LVL3STAT": task_specific_gos_level3_status,
                "LAMPSTAT": task_specific_gos_level3_lamp_status,
                "LVL2STAT": task_specific_gos_polarizer_status,
                "POLANGLE": task_specific_gos_polarizer_angle,
                "LVL1STAT": task_specific_gos_retarder_status,
                "RETANGLE": task_specific_gos_retarder_angle,
                "LVL0STAT": task_specific_gos_level0_status,
            },
        }

        # Remove specific headers from dark frames as they don't constants to fill them
        if task_type == TaskName.dark:
            for key in ["TELTRACK", "TTBLTRCK", "TELSCAN"]:
                del dataset_extra_header[DatasetExtraHeaderSection.common][key]

        # Remove specific headers from polcal frames as they don't have constants to fill them
        if task_type == TaskName.polcal:
            for key in [
                "LVL3STAT",
                "LAMPSTAT",
                "LVL2STAT",
                "POLANGLE",
                "LVL1STAT",
                "RETANGLE",
                "LVL0STAT",
            ]:
                del dataset_extra_header[DatasetExtraHeaderSection.gos][key]

        return dataset_extra_header

    def build_dataset_extra_header(
        self,
        sections: list[DatasetExtraHeaderSection],
        filename: str,
        task_type: TaskName,
        extra_name: DatasetExtraType,
        total_exposure: float | None = None,
        readout_exposure: float | None = None,
        end_time: str | None = None,
    ) -> fits.Header:
        """Build FITS header for dataset extra file."""
        header = fits.Header()
        all_section_headers = self.dataset_extra_headers(
            filename=filename,
            task_type=task_type,
            total_exposure=total_exposure,
            readout_exposure=readout_exposure,
            extra_name=extra_name,
            end_time=end_time,
        )
        for section in sections:
            header.update(all_section_headers[section].items())
        return header

    def format_extra_filename(self, extra_name: DatasetExtraType | str, detail: str | None = None):
        """Format the filename of dataset extras for consistency."""
        base_filename = f"{self.constants.instrument}_{self.constants.dataset_id}_{extra_name.replace(' ', '-')}"
        if detail:
            base_filename += "_" + detail
        filename_counter = str(self.filename_counter.increment(base_filename))
        return f"{base_filename}_{filename_counter}.fits"

    def assemble_and_write_dataset_extra(
        self,
        data: np.ndarray | list[np.ndarray],
        header: fits.Header | list[fits.Header],
        filename: str,
    ):
        """Given the data and header information, write the dataset extra."""
        if isinstance(data, list) and isinstance(header, list):
            if len(data) != len(header):
                raise ValueError(
                    f"{len(data)} data arrays were provided with {len(header)} headers. These must be equal."
                )
        if isinstance(data, np.ndarray):
            data = [data]
        if isinstance(header, fits.Header):
            header = [header]
        hdus = [fits.PrimaryHDU()]  # The first HDU in the list is an empty PrimaryHDU
        for i, data_array in enumerate(data):
            tile_size = self.compute_tile_size_for_array(data_array)
            hdu = fits.CompImageHDU(header=header[i], data=data_array, tile_shape=tile_size)
            formatted_header = reformat_dataset_extra_header(hdu.header)
            hdu = fits.CompImageHDU(header=formatted_header, data=hdu.data, tile_shape=tile_size)
            hdus.append(hdu)
        self.write(
            data=fits.HDUList(hdus),
            tags=[Tag.extra(), Tag.output()],
            encoder=fits_hdulist_encoder,
            relative_path=filename,
        )
        self.update_framevol(relative_path=filename)

        # Check that the written file passes spec 214 validation if requested
        if self.validate_l1_on_write:
            spec_extras_validator.validate(self.scratch.absolute_path(filename), extra=False)

    @abstractmethod
    def run(self) -> None:
        """
        For each dataset extra.

        * Gather the source data in whatever manner is necessary
        * Build a header using the `build_dataset_extra_header` method to help with header construction
        * Write the dataset extra using `assemble_and_write_dataset_extra()`
        """
