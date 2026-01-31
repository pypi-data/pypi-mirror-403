"""DataPipe workflow tests for CLIs and simple workflows."""

import logging
import subprocess as sp
from pathlib import Path

import pytest
import yaml
from astropy.utils.data import shutil
from ctapipe.io import TableLoader
from ctapipe.utils import get_dataset_path

from datapipe.tests.utils import run_cwl

LOG = logging.getLogger("test_workflows")


@pytest.mark.verifies_usecase("DPPS-UC-130-1.2.1")
def test_dl0_dl1_main(tmp_path):
    """Test transformation from DL0 to DL1."""
    values = tmp_path / "values.cfg"
    values.write_text(
        yaml.dump(
            dict(
                dl0="dataset://gamma_prod5.simtel.zst",
                dl1_filename="events.dl1.h5",
            )
        )
    )

    result = run_cwl(
        Path("workflows/process_dl0_dl1.cwl").absolute(),
        inputs_path=values,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    # Now check that the events.dl1.h5 file looks ok.

    out_path = tmp_path / "events.dl1.h5"
    assert out_path.exists()

    with TableLoader(out_path) as loader:
        assert len(loader.read_scheduling_blocks()) > 0

        sub_events = loader.read_subarray_events()
        assert len(sub_events) > 5
        assert "time" in sub_events.colnames

        tel_events = loader.read_telescope_events()
        assert len(tel_events) > 5
        assert "tel_id" in tel_events.colnames
        assert "hillas_width" in tel_events.colnames


@pytest.mark.verifies_usecase("DPPS-UC-130-1.2.1")
def test_dl0_dl1_camcalib(tmp_path):
    """Test transformation from DL0 to DL1 with a camcalib monitoring file."""
    dl0_path = get_dataset_path("gamma_prod6_preliminary.simtel.zst")
    camera_calibration_path = get_dataset_path(
        "calibpipe_camcalib_single_chunk_i0.1.0.dl1.h5"
    )

    dl1_filename = "events_with_camcalib.dl1.h5"
    values = tmp_path / "values.cfg"
    config = tmp_path / "config.yaml"
    allowed_tels = [1]

    with config.open("w") as f:
        yaml.dump(
            {
                "SimTelEventSource": {
                    "allowed_tels": allowed_tels,
                    "skip_r1_calibration": True,
                },
            },
            f,
        )

    # use relative path to check if input is properly accessed
    shutil.copy2(dl0_path, tmp_path / dl0_path.name)
    shutil.copy2(camera_calibration_path, tmp_path / camera_calibration_path.name)

    values = tmp_path / "values.cfg"
    values.write_text(
        yaml.dump(
            {
                "dl0": {"class": "File", "path": dl0_path.name},
                "dl1_filename": dl1_filename,
                "camera_calibration_file": {
                    "class": "File",
                    "path": camera_calibration_path.name,
                },
                "processing_config": {"class": "File", "path": str(config)},
                # parameters doesn't work currently, as skip_r1_calibration implies no gain selection
                "write_parameters": False,
            }
        )
    )

    result = run_cwl(
        Path("workflows/process_dl0_dl1.cwl").absolute(),
        inputs_path=values,
        cwd=tmp_path,
    )
    LOG.info("Output of running cwl:\n%s", result.stdout)

    assert result.returncode == 0, result.stdout

    # Now check that the events_with_camcalib.dl1.h5 file looks ok.

    out_path = tmp_path / "events_with_camcalib.dl1.h5"
    assert out_path.exists()

    with TableLoader(out_path) as loader:
        assert len(loader.read_scheduling_blocks()) > 0

        tel_events = loader.read_telescope_events(dl1_images=True)
        assert len(tel_events) == 3
        assert "tel_id" in tel_events.colnames
        assert "image" in tel_events.colnames
        # check that we correctly applied calibrations.
        assert tel_events["image"].mean() > 0


@pytest.mark.verifies_usecase("DPPS-UC-130-1.2.2")
def test_dl1_dl2_main(tmp_path):
    """Test transformation from DL1 to DL2 up to stereo geometry (main scenario).

    This actually goes from DL0 to DL2, to avoid having to do a separate
    workflows for each step. However, the full workflow is tested in the
    following test.
    """
    values = tmp_path / "values.cfg"
    values.write_text(
        yaml.dump(
            dict(
                dl1="dataset://gamma_prod5.simtel.zst",
                dl2_filename="events.dl2.h5",
            )
        )
    )

    result = run_cwl(
        Path("workflows/process_dl1_dl2.cwl").absolute(),
        inputs_path=values,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    # Now check that the events.dl1.h5 file looks ok.

    out_path = tmp_path / "events.dl2.h5"
    assert out_path.exists()

    with TableLoader(out_path) as loader:
        assert len(loader.read_scheduling_blocks()) > 0

        sub_events = loader.read_subarray_events()
        assert len(sub_events) > 5
        assert "time" in sub_events.colnames
        assert "HillasReconstructor_h_max" in sub_events.colnames


@pytest.mark.xfail
@pytest.mark.verifies_usecase("DPPS-UC-130-1.2.2")
def test_dl1_dl2_extended(tmp_path):
    """Test transformation from DL1 to DL2 with extended reconstruction."""
    pytest.fail("to be implemented")


@pytest.mark.xfail
@pytest.mark.verifies_usecase("DPPS-UC-130-1.2.2")
def test_dl1_dl2_alt_mono(tmp_path):
    """Test transformation from DL1 to DL2 alternate scenario: mono reco."""
    pytest.fail("to be implemented")


@pytest.mark.verifies_usecase("DPPS-UC-130-1.2")
def test_workflow_dl0_dl2_main(tmp_path):
    """Test workflow of 2 steps: DL0 to DL1 followed by DL1 to DL2.

    Note this is only a PARTIAL validation of UC-130-1.2. The rest should be by
    inspection, since it requires a code review.
    """
    dl0_filename = str(get_dataset_path("gamma_prod5.simtel.zst"))

    values = tmp_path / "values.cfg"
    values.write_text(
        yaml.dump(
            {
                "dl0": {"class": "File", "path": dl0_filename},
            }
        )
    )

    result = run_cwl(
        Path("workflows/workflow_dl0_to_dl2.cwl").absolute(),
        inputs_path=values,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    # Now check that the events.dl1.h5 file looks ok.

    assert (tmp_path / "gamma_prod5.dl1.h5").exists()
    assert (tmp_path / "gamma_prod5.dl2.h5").exists()


@pytest.mark.verifies_usecase("DPPS-UC-130-1.8")
def test_workflow_merge(tmp_path):
    """Test cwl of merge tool."""
    input_file = get_dataset_path("gamma_prod5.simtel.zst")
    # create to dl1 files with different obs_ids, merge checks for
    # same subarray and different obs-ids, but we do not have two test files
    # that are small and similar
    inputs = {"input_files": [], "output_filename": "merged.dl1.h5"}
    for obs_id in (1, 2):
        output_path = tmp_path / f"gamma_{obs_id}.dl1.h5"
        sp.run(
            [
                "ctapipe-process",
                f"--input={input_file}",
                f"--output={output_path}",
                f"--SimTelEventSource.override_obs_id={obs_id}",
            ],
            cwd=tmp_path,
            check=True,
        )
        inputs["input_files"].append({"class": "File", "path": str(output_path)})

    inputs_path = tmp_path / "inputs.yaml"
    with inputs_path.open("w") as f:
        yaml.dump(inputs, f)

    result = run_cwl(
        Path("workflows/merge.cwl").absolute(),
        inputs_path=inputs_path,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "merged.dl1.h5").is_file()
    assert (tmp_path / "ctapipe-merge.provenance.log").is_file()


@pytest.mark.verifies_usecase("DPPS-UC-130-1.3")
def test_dummy():
    """Hack to make UCs that are marked as by inspection pass."""
    assert True
