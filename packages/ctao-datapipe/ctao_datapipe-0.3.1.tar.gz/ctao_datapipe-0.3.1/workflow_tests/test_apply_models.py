#!/usr/bin/env python3

"""Tests of IRF workflows."""

import json
from pathlib import Path

import numpy as np
import pytest
from ctapipe.io import TableLoader

from datapipe.tests.utils import run_cwl


@pytest.mark.verifies_usecase("DPPS-UC-130-1.4")
def test_apply(
    tmp_path,
    gammas_dl2_only_geom_path: Path,
    energy_model_path: Path,
    classifier_model_path: Path,
):
    """Test optimize UC."""
    config_file = tmp_path / "apply_models-job.json"
    out_file = "applied.dl2.h5"
    config_file.write_text(
        json.dumps(
            dict(
                events={"class": "File", "path": str(gammas_dl2_only_geom_path)},
                models=[
                    {"class": "File", "path": str(energy_model_path)},
                    {"class": "File", "path": str(classifier_model_path)},
                ],
                output_filename=out_file,
            ),
            indent=2,
        )
    )

    out_path = tmp_path / out_file

    result = run_cwl(
        Path("workflows/apply_models.cwl").absolute(),
        inputs_path=config_file,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    with TableLoader(out_path, dl2=True) as loader:
        sub_events = loader.read_subarray_events()
        assert len(sub_events) > 5, "No or too few events in output"

        for col in [
            "RandomForestRegressor_energy",
            "RandomForestClassifier_prediction",
        ]:
            assert col in sub_events.colnames
            assert len(np.isfinite(sub_events[col])) > 0, "values are all NaN"
