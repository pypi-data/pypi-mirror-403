#!/usr/bin/env python3
"""Test model training workflows."""

import json
from pathlib import Path

import numpy as np
import pytest
from ctapipe.io import TableLoader, read_table
from ctapipe.reco.reconstructor import ReconstructionProperty, Reconstructor

from datapipe.tests.utils import run_cwl

TRAINING_CONFIG = """
TrainEnergyRegressor:
  CrossValidator:
    n_cross_validations: 5

  EnergyRegressor:
    model_cls: ExtraTreesRegressor
    log_target: True

    model_config:
      n_estimators: 10
      max_depth: 10
      n_jobs: -1

    features:
      - hillas_intensity
      - HillasReconstructor_tel_impact_distance

TrainParticleClassifier:
  CrossValidator:
    n_cross_validations: 5

  ParticleClassifier:
    model_cls: ExtraTreesClassifier
    model_config:
      n_estimators: 10
      max_depth: 10
      n_jobs: -1

    features:
      - hillas_intensity
      - hillas_width
      - HillasReconstructor_tel_impact_distance

TrainDispReconstructor:
  CrossValidator:
    n_cross_validations: 5

  DispReconstructor:
    norm_cls: ExtraTreesRegressor
    sign_cls: ExtraTreesClassifier
    norm_config:
      n_estimators: 10
      max_depth: 10
      n_jobs: -1
    sign_config:
      n_estimators: 10
      max_depth: 10
      n_jobs: -1

    features:
      - hillas_intensity
      - hillas_width
      - hillas_r
"""


@pytest.fixture
def training_config_file(tmp_path):
    """Create a YAML config file for use with ctapipe training tools."""
    training_config_file = tmp_path / "train_energy.conf.yaml"
    training_config_file.write_text(TRAINING_CONFIG)
    return training_config_file


@pytest.mark.verifies_usecase("DPPS-UC-130-1.3.1")
def test_train_energy_model(tmp_path, gammas_dl2_only_geom_path, training_config_file):
    """Test training an energy regressor."""
    gammas = gammas_dl2_only_geom_path
    model_path = tmp_path / "energy_reco_model.pkl"  # the default filename
    cross_validation_path = tmp_path / "energy_cross_validation.h5"

    job_file = tmp_path / "train_energy_model-job.json"
    job_file.write_text(
        json.dumps(
            dict(
                config={"class": "File", "path": str(training_config_file.name)},
                gamma_events={"class": "File", "path": str(gammas)},
            ),
            indent=2,
        )
    )

    result = run_cwl(
        Path("workflows/train_energy_model.cwl").absolute(),
        inputs_path=job_file,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    assert model_path.exists(), f"expected model file: {model_path}"
    assert cross_validation_path.exists()

    # Success item 1: try to load the model and reconstruct some events
    #
    with TableLoader(gammas) as loader:
        reco = Reconstructor.from_name(
            "EnergyRegressor",
            subarray=loader.subarray,
            model_cls="ExtraTreesRegressor",
            load_path=model_path,
        )
        data = loader.read_telescope_events_by_id(1)[1]
        result = reco.predict_table(loader.subarray.telescope_types[0], data)

        assert ReconstructionProperty.ENERGY in result

        prediction = result[ReconstructionProperty.ENERGY]

        # Now just check that there are values and that they have some
        # reasonable mean
        parameter = "ExtraTreesRegressor_tel_energy"
        assert parameter in prediction.colnames
        assert np.count_nonzero(prediction[parameter]) > 10
        assert np.nanmean(prediction[parameter]) > 0.1

    # Success item 2: check cross_validation exists:
    for tel in loader.subarray.telescope_types:
        cv_table = read_table(cross_validation_path, f"/cv_predictions/{tel}")
        assert len(cv_table) > 1000
        assert "ExtraTreesRegressor_energy" in cv_table.columns


@pytest.mark.verifies_usecase("DPPS-UC-130-1.3.2")
def test_train_gammaness_model(
    tmp_path,
    gammas_dl2_only_geom_path,
    protons_dl2_path,
    training_config_file,
):
    """Test training an energy regressor."""
    gammas = gammas_dl2_only_geom_path
    protons = protons_dl2_path
    cross_validation_path = tmp_path / "gammaness_cross_validation.h5"

    job_file = tmp_path / "train_gammaness_model-job.json"
    job_file.write_text(
        json.dumps(
            dict(
                config={"class": "File", "path": str(training_config_file.name)},
                gamma_events={"class": "File", "path": str(gammas)},
                background_events={"class": "File", "path": str(protons)},
            ),
            indent=2,
        )
    )

    model_path = tmp_path / "gammaness_reco_model.pkl"  # the default filename
    result = run_cwl(
        Path("workflows/train_gammaness_model.cwl").absolute(),
        inputs_path=job_file,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    # Success item 1: load the events and see if we can predict

    with TableLoader(gammas) as loader:
        reco = Reconstructor.from_name(
            "ParticleClassifier",
            subarray=loader.subarray,
            model_cls="ExtraTreesClassifier",
            load_path=model_path,
        )
        data = loader.read_telescope_events_by_id(1)[1]
        result = reco.predict_table(loader.subarray.telescope_types[0], data)

        assert ReconstructionProperty.PARTICLE_TYPE in result

        prediction = result[ReconstructionProperty.PARTICLE_TYPE]

        # Now just check that there are values and that they have some
        # reasonable mean
        parameter = "ExtraTreesClassifier_tel_prediction"
        assert parameter in prediction.colnames
        assert np.count_nonzero(prediction[parameter]) > 10
        assert np.nanmean(prediction[parameter]) > 0.1

    # Success item 2: check cross_validation exists:
    for tel in loader.subarray.telescope_types:
        cv_table = read_table(cross_validation_path, f"/cv_predictions/{tel}")
        assert len(cv_table) > 1000
        assert "ExtraTreesClassifier_prediction" in cv_table.columns


@pytest.mark.verifies_usecase("DPPS-UC-130-1.3.3")
def test_train_disp_model(tmp_path, gammas_dl2_only_geom_path, training_config_file):
    """Test training an energy regressor."""
    gammas = gammas_dl2_only_geom_path
    cross_validation_path = tmp_path / "disp_cross_validation.h5"

    job_file = tmp_path / "train_disp_model-job.json"
    job_file.write_text(
        json.dumps(
            dict(
                config={"class": "File", "path": str(training_config_file.name)},
                gamma_events={"class": "File", "path": str(gammas)},
            ),
            indent=2,
        )
    )

    model_path = tmp_path / "disp_reco_model.pkl"  # the default filename
    result = run_cwl(
        Path("workflows/train_disp_model.cwl").absolute(),
        inputs_path=job_file,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    # Success item 1: try to load it back up and predict

    with TableLoader(gammas) as loader:
        reco = Reconstructor.from_name(
            "DispReconstructor",
            subarray=loader.subarray,
            norm_cls="ExtraTreesRegressor",
            sign_cls="ExtraTreesClassifier",
            load_path=model_path,
        )
        data = loader.read_telescope_events_by_id(1)[1]
        result = reco.predict_table(loader.subarray.telescope_types[0], data)

        assert ReconstructionProperty.DISP in result

        prediction = result[ReconstructionProperty.DISP]

        # Now just check that there are values and that they have some
        # reasonable mean
        parameter = "disp_tel_parameter"
        assert parameter in prediction.colnames
        assert np.count_nonzero(prediction[parameter]) > 10

    # Success item 2: check cross_validation exists:

    for tel in loader.subarray.telescope_types:
        cv_table = read_table(cross_validation_path, f"/cv_predictions/{tel}")
        assert len(cv_table) > 1000
        assert "disp_parameter" in cv_table.columns
        assert "disp_sign_score" in cv_table.columns
