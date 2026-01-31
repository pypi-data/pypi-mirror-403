from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from dkist_processing_common._util.scratch import WorkflowFileSystem
from dkist_processing_common.codecs.fits import fits_array_decoder
from dkist_processing_common.codecs.fits import fits_array_encoder
from dkist_processing_common.models.extras import DatasetExtraHeaderSection
from dkist_processing_common.models.extras import DatasetExtraType
from dkist_processing_common.models.tags import Tag
from dkist_processing_common.models.task_name import TaskName
from dkist_processing_common.tasks.write_extra import WriteL1DatasetExtras
from dkist_processing_common.tests.mock_metadata_store import RecipeRunResponseMapping
from dkist_processing_common.tests.mock_metadata_store import fake_gql_client_factory
from dkist_processing_common.tests.mock_metadata_store import make_default_recipe_run_response


@dataclass
class FakeConstantDb:
    INSTRUMENT: str = "VBI"
    DATASET_ID: str = "DATASETID"
    AVERAGE_CADENCE: float = 10.0
    MINIMUM_CADENCE: float = 10.0
    MAXIMUM_CADENCE: float = 10.0
    VARIANCE_CADENCE: float = 0.0
    STOKES_PARAMS: tuple = ("I", "Q", "U", "V")
    PROPOSAL_ID: str = "PROPID1"
    EXPERIMENT_ID: str = "EXPERID1"
    CAMERA_ID: str = "CAMERA1"
    CAMERA_NAME: str = "Camera One"
    CAMERA_BIT_DEPTH: int = 16
    HARDWARE_BINNING_X: int = 1
    HARDWARE_BINNING_Y: int = 1
    SOFTWARE_BINNING_X: int = 1
    SOFTWARE_BINNING_Y: int = 1
    HLS_VERSION: str = "1.8"
    WAVELENGTH: float = 854.2
    # Dark
    DARK_OBSERVING_PROGRAM_EXECUTION_IDS: tuple = ("OP1", "OP2", "OP3")
    DARK_DATE_BEGIN: str = "2023-01-01T00:00:00"
    DARK_DATE_END: str = "2023-01-01T01:00:00"
    DARK_TELESCOPE_TRACKING_MODE: str = "None"
    DARK_COUDE_TABLE_TRACKING_MODE: str = "fixed coude table angle"
    DARK_TELESCOPE_SCANNING_MODE: str = "None"
    DARK_AVERAGE_LIGHT_LEVEL: float = 5.0
    DARK_AVERAGE_TELESCOPE_ELEVATION: float = 45.0
    DARK_AVERAGE_COUDE_TABLE_ANGLE: float = 2.0
    DARK_AVERAGE_TELESCOPE_AZIMUTH: float = 180.0
    DARK_GOS_LEVEL3_STATUS: str = "clear"
    DARK_GOS_LEVEL3_LAMP_STATUS: str = "off"
    DARK_GOS_POLARIZER_STATUS: str = "clear"
    DARK_GOS_POLARIZER_ANGLE: str = "0.0"
    DARK_GOS_RETARDER_STATUS: str = "clear"
    DARK_GOS_RETARDER_ANGLE: str = "0.0"
    DARK_GOS_LEVEL0_STATUS: str = "DarkShutter"
    # Solar Gain
    SOLAR_GAIN_OBSERVING_PROGRAM_EXECUTION_IDS: tuple = ("OP1", "OP2", "OP3")
    SOLAR_GAIN_DATE_BEGIN: str = "2023-01-01T00:00:00"
    SOLAR_GAIN_DATE_END: str = "2023-01-01T01:00:00"
    SOLAR_GAIN_NUM_RAW_FRAMES_PER_FPA: int = 1
    SOLAR_GAIN_TELESCOPE_TRACKING_MODE: str = "None"
    SOLAR_GAIN_COUDE_TABLE_TRACKING_MODE: str = "fixed coude table angle"
    SOLAR_GAIN_TELESCOPE_SCANNING_MODE: str = "None"
    SOLAR_GAIN_AVERAGE_LIGHT_LEVEL: float = 5.0
    SOLAR_GAIN_AVERAGE_TELESCOPE_ELEVATION: float = 45.0
    SOLAR_GAIN_AVERAGE_COUDE_TABLE_ANGLE: float = 2.0
    SOLAR_GAIN_AVERAGE_TELESCOPE_AZIMUTH: float = 180.0
    SOLAR_GAIN_GOS_LEVEL3_STATUS: str = "clear"
    SOLAR_GAIN_GOS_LEVEL3_LAMP_STATUS: str = "off"
    SOLAR_GAIN_GOS_POLARIZER_STATUS: str = "clear"
    SOLAR_GAIN_GOS_POLARIZER_ANGLE: str = "0.0"
    SOLAR_GAIN_GOS_RETARDER_STATUS: str = "clear"
    SOLAR_GAIN_GOS_RETARDER_ANGLE: str = "0.0"
    SOLAR_GAIN_GOS_LEVEL0_STATUS: str = "DarkShutter"
    # Polcal
    POLCAL_OBSERVING_PROGRAM_EXECUTION_IDS: tuple = ("OP1", "OP2", "OP3")
    POLCAL_DATE_BEGIN: str = "2023-01-01T00:00:00"
    POLCAL_DATE_END: str = "2023-01-01T01:00:00"
    POLCAL_NUM_RAW_FRAMES_PER_FPA: int = 1
    POLCAL_TELESCOPE_TRACKING_MODE: str = "None"
    POLCAL_COUDE_TABLE_TRACKING_MODE: str = "fixed coude table angle"
    POLCAL_TELESCOPE_SCANNING_MODE: str = "None"
    POLCAL_AVERAGE_LIGHT_LEVEL: float = 5.0
    POLCAL_AVERAGE_TELESCOPE_ELEVATION: float = 45.0
    POLCAL_AVERAGE_COUDE_TABLE_ANGLE: float = 2.0
    POLCAL_AVERAGE_TELESCOPE_AZIMUTH: float = 180.0


class ConstructDatasetExtrasTest(WriteL1DatasetExtras):
    def run(self):
        # Make a dataset extra for each task type

        for task_type in [
            TaskName.dark,
            TaskName.solar_gain,
        ]:
            filename = self.format_extra_filename(task_type, detail="BEAM1")
            data = next(
                self.read(
                    tags=[Tag.task(task_type), Tag.intermediate()], decoder=fits_array_decoder
                )
            )
            header = self.build_dataset_extra_header(
                sections=[
                    DatasetExtraHeaderSection.common,
                    DatasetExtraHeaderSection.aggregate,
                    DatasetExtraHeaderSection.iptask,
                    DatasetExtraHeaderSection.gos,
                ],
                filename=filename,
                task_type=task_type,
                total_exposure=0.058,
                readout_exposure=0.029,
                extra_name=(
                    DatasetExtraType.dark if task_type == "DARK" else DatasetExtraType.solar_gain
                ),
                end_time="2025-01-01T00:00:00",
            )

            self.assemble_and_write_dataset_extra(data=data, header=header, filename=filename)

        task_type = TaskName.polcal
        filename = self.format_extra_filename(task_type, detail="BEAM1")
        data = next(
            self.read(tags=[Tag.task(task_type), Tag.intermediate()], decoder=fits_array_decoder)
        )
        header = self.build_dataset_extra_header(
            sections=[
                DatasetExtraHeaderSection.common,
                DatasetExtraHeaderSection.aggregate,
                DatasetExtraHeaderSection.iptask,
                DatasetExtraHeaderSection.gos,
            ],
            filename=filename,
            task_type=task_type,
            total_exposure=0.058,
            readout_exposure=0.029,
            extra_name=DatasetExtraType.demodulation_matrices,
            end_time="2025-01-01T00:00:00",
        )
        self.assemble_and_write_dataset_extra(data=data, header=header, filename=filename)


@pytest.fixture()
def construct_dataset_extras_task(request, recipe_run_id, tmp_path):
    with ConstructDatasetExtrasTest(
        recipe_run_id=recipe_run_id,
        workflow_name="workflow_name",
        workflow_version="workflow_version",
    ) as task:
        task.scratch = WorkflowFileSystem(recipe_run_id=recipe_run_id, scratch_base_path=tmp_path)
        # Write an intermediate product to be used as the source for each dataset extra
        for task_type in [
            TaskName.dark,
            TaskName.solar_gain,
            TaskName.polcal,
        ]:
            task.write(
                data=np.random.random(size=(1, 128, 128)),
                tags=[Tag.task(task_type), Tag.intermediate()],
                encoder=fits_array_encoder,
            )
        task.constants._update(asdict(FakeConstantDb()))
        yield task
        task._purge()


@pytest.fixture
def fake_gql_client_default_configuration():
    """Create GraphQL client Mock that returns result without recipe run configuration."""
    recipe_run_response = make_default_recipe_run_response()
    recipe_run_response.configuration = None
    new_response_mapping = RecipeRunResponseMapping(response=recipe_run_response)
    FakeGQLClientDefaultConfiguration = fake_gql_client_factory(
        response_mapping_override=new_response_mapping
    )

    return FakeGQLClientDefaultConfiguration


def test_construct_dataset_extras(
    construct_dataset_extras_task, mocker, fake_gql_client_default_configuration
):
    """
    Given: A ConstructDatasetExtras task with source data
    When: Running the ConstructDatasetExtras task
    Then: A dataset extra files are produced with expected header values
    """
    mocker.patch(
        "dkist_processing_common.tasks.mixin.metadata_store.GraphQLClient",
        new=fake_gql_client_default_configuration,
    )
    task = construct_dataset_extras_task
    task()
    dataset_extra_files = list(task.read(tags=[Tag.output(), Tag.extra()]))
    assert len(dataset_extra_files) == 3
    for filename in dataset_extra_files:
        split_filename = Path(filename).name.split("_")
        assert split_filename[0] == "VBI"
        assert split_filename[1] == task.constants.dataset_id
        assert split_filename[-2] == "BEAM1"
        assert split_filename[-1] == "1.fits"
        hdul = fits.open(filename)
        for i in range(1, len(hdul)):
            assert isinstance(hdul[i], fits.CompImageHDU)
            header = hdul[i].header
            assert header["LINEWAV"] == 854.2
            assert header["INSTRUME"] == "VBI"
            assert header["ATAZIMUT"] == 180.0
            assert header["FRAMEVOL"] is not None
            assert header["IDSOBSID"] == 2
            assert header["XPOSURE"] == 0.058
            assert header["OBSPR_ID"] == "OP1"
            assert header["EXTOBSID"] == "OP2,OP3"
            assert header["EXTNAME"] in ["DARK", "SOLAR GAIN", "DEMODULATION MATRICES"]
            if header["IPTASK"] == "POLCAL":
                assert "POLANGLE" not in header
            else:
                assert header.get("POLANGLE") == "0.0"
                assert header.get("RETANGLE") == "0.0"
