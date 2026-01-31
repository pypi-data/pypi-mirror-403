#!/usr/bin/env python3

"""Configure tests for CWL."""

import pytest
from ctapipe.utils import get_dataset_path

URL = "https://minio-cta.zeuthen.desy.de/dpps-testdata-public/data/datapipe-test-data/"


@pytest.fixture(scope="session")
def gammas_dl2_path():
    """Sample DL2 gammas file."""
    return get_dataset_path("gamma_test_geo_en_cl.dl2.h5", url=URL)


@pytest.fixture(scope="session")
def gammas_dl2_only_geom_path():
    """Sample DL2 gammas file with only reconstruccted geometry columns.."""
    return get_dataset_path("gamma_test_geo.dl2.h5", url=URL)


@pytest.fixture(scope="session")
def electrons_dl2_path():
    """Sample DL2 electrons file."""
    return get_dataset_path("electron_test_geo_en_cl.dl2.h5", url=URL)


@pytest.fixture(scope="session")
def protons_dl2_path():
    """Sample DL2 protons file."""
    return get_dataset_path("proton_test_geo_en_cl.dl2.h5", url=URL)


@pytest.fixture(scope="session")
def event_selection_path():
    """Sample event cuts file as output from ctapipe-optimize-event-selection."""
    return get_dataset_path("event_selection.fits", url=URL)


@pytest.fixture(scope="session")
def energy_model_path():
    """Sample gamma energy reconstruction model."""
    return get_dataset_path("energy_model.pkl", url=URL)


@pytest.fixture(scope="session")
def classifier_model_path():
    """Sample gammaness reconstruction model."""
    return get_dataset_path("classifier_model.pkl", url=URL)
