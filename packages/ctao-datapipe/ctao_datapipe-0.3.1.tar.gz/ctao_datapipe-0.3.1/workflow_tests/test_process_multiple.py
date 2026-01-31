"""Tests for the cwl workflow for processing multiple files and then merge them."""

import logging
import subprocess as sp
from pathlib import Path

import yaml
from ctapipe.utils import get_dataset_path

from datapipe.tests.utils import run_cwl

log = logging.getLogger(__name__)


def test_workflow_process_multiple(tmp_path):
    """Test cwl workflow for processing multiple files, then merge."""
    input_file = get_dataset_path("gamma_prod5.simtel.zst")
    # create to dl1 files with different obs_ids, merge checks for
    # same subarray and different obs-ids, but we do not have two test files
    # that are small and similar
    inputs = {
        "input_files": [],
        "output_filename": "merged.dl1.h5",
    }
    for obs_id in (1, 2):
        output_path = tmp_path / f"gamma_{obs_id}.dl1_img.h5"
        sp.run(
            [
                "ctapipe-process",
                f"--input={input_file}",
                f"--output={output_path}",
                f"--SimTelEventSource.override_obs_id={obs_id}",
                "--write-images",
                "--no-write-parameters",
            ],
            check=True,
        )
        inputs["input_files"].append({"class": "File", "path": str(output_path)})

    inputs_path = tmp_path / "inputs.yaml"
    with inputs_path.open("w") as f:
        yaml.dump(inputs, f)

    cwl_path = tmp_path / "cwl_run"
    cwl_path.mkdir()

    result = run_cwl(
        Path("workflows/process_dl0_dl1_multiple.cwl").absolute(),
        inputs_path=inputs_path,
        cwd=cwl_path,
    )
    log.info("cwltool output:\n%s", result.stdout)
    assert result.returncode == 0, result.stdout
    assert (cwl_path / "merged.dl1.h5").is_file()
    assert (cwl_path / "ctapipe-merge.provenance.log").is_file()

    for obs_id in (1, 2):
        name = f"gamma_{obs_id}.dl1.h5"
        # intermediate output files shouldn't be in the output
        assert not (cwl_path / name).is_file()
        # but log and provlog should
        assert (cwl_path / f"{name}.provlog").is_file()
