#!/usr/bin/env python3

"""Tests of IRF workflows."""

import json
from pathlib import Path

import pytest
from astropy.table import Table

from datapipe.tests.utils import run_cwl


@pytest.mark.verifies_usecase("DPPS-UC-130-1.9")
def test_optimize(
    tmp_path, gammas_dl2_path: Path, protons_dl2_path: Path, electrons_dl2_path: Path
):
    """Test optimize UC."""
    config_file = tmp_path / "optimize-job.json"
    config_file.write_text(
        json.dumps(
            dict(
                gammas={"class": "File", "path": str(gammas_dl2_path)},
                electrons={"class": "File", "path": str(electrons_dl2_path)},
                protons={"class": "File", "path": str(protons_dl2_path)},
                output_filename="event_selection.fits",
            ),
            indent=2,
        )
    )

    result = run_cwl(
        Path("workflows/optimize.cwl").absolute(),
        inputs_path=config_file,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    # look inside the output file for expected HDUs:
    for hdu in ["RAD_MAX", "GH_CUTS", "VALID_ENERGY", "VALID_OFFSET"]:
        Table.read(tmp_path / "event_selection.fits", hdu=hdu)


@pytest.mark.verifies_usecase("DPPS-UC-130-1.6")
def test_compute_irfs(
    tmp_path,
    gammas_dl2_path: Path,
    protons_dl2_path: Path,
    electrons_dl2_path: Path,
    event_selection_path: Path,
):
    """Test compute irfs UC."""
    config_file = tmp_path / "compute_irf-job.json"
    config_file.write_text(
        json.dumps(
            dict(
                gammas={"class": "File", "path": str(gammas_dl2_path)},
                electrons={"class": "File", "path": str(electrons_dl2_path)},
                protons={"class": "File", "path": str(protons_dl2_path)},
                event_selection={"class": "File", "path": str(event_selection_path)},
                output_filename="irf.fits.gz",
                output_metrics_filename="performance_metrics.fits",
            ),
            indent=2,
        )
    )

    result = run_cwl(
        Path("workflows/compute_irf.cwl").absolute(),
        inputs_path=config_file,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    # look inside the output file for expected HDUs:
    for hdu in ["EFFECTIVE AREA", "ENERGY DISPERSION", "PSF", "BACKGROUND"]:
        Table.read(tmp_path / "irf.fits.gz", hdu=hdu)

    for hdu in ["SENSITIVITY", "ANGULAR RESOLUTION"]:
        tab = Table.read(tmp_path / "performance_metrics.fits", hdu=hdu)
        assert "ENERG_LO" in tab.colnames


def test_both(
    tmp_path,
    gammas_dl2_path: Path,
    protons_dl2_path: Path,
    electrons_dl2_path: Path,
    event_selection_path: Path,
):
    """Test a workflow combining Optimize and Compute."""
    config_file = tmp_path / "workflow_optimize_and_irf-job.json"
    config_file.write_text(
        json.dumps(
            dict(
                gammas_optimize={"class": "File", "path": str(gammas_dl2_path)},
                electrons_optimize={"class": "File", "path": str(electrons_dl2_path)},
                protons_optimize={"class": "File", "path": str(protons_dl2_path)},
                gammas_irf={"class": "File", "path": str(gammas_dl2_path)},
                electrons_irf={"class": "File", "path": str(electrons_dl2_path)},
                protons_irf={"class": "File", "path": str(protons_dl2_path)},
                event_selection={"class": "File", "path": str(event_selection_path)},
                analysis_name="ctao-example",
            ),
            indent=2,
        )
    )

    result = run_cwl(
        Path("workflows/workflow_optimize_and_irf.cwl").absolute(),
        inputs_path=config_file,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout

    assert (tmp_path / "ctao-example.irf.fits").exists()
    assert (tmp_path / "ctao-example.performance.fits").exists()
    assert (tmp_path / "ctao-example.event_selection.fits").exists()
