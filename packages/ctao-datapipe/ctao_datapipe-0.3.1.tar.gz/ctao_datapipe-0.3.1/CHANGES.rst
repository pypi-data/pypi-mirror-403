datapipe 0.3.1 (2026-01-28)
---------------------------

Maintenance
~~~~~~~~~~~

- Update ctapipe to 0.29.0 [`!55 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/55>`__]

datapipe 0.3 (2025-11-18)
-------------------------

New Features
~~~~~~~~~~~~

- Added test for DL0 to DL1 transformation with a camcalib monitoring file from
  calibpipe. [`!47 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/47>`__]

- Added CWL workflows for training gammaness, energy, and disp reconstruction
  models [`!48 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/48>`__]

- Add a CWL workflow that runs the dl0 to dl1 step on multiple input files and
  then merges the results into a single final output file. [`!27
  <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/27>`__]

- Add new options to the process_dl0_dl1.cwl workflow:

  - camera_calibration_file for calib-pipe produced camera calibration coefficients
  - write_images to switch storing of images on or off
  - write_parameters to switch storing of parameters on or off [`!53 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/53>`__]


Maintenance
~~~~~~~~~~~

- Use latest dependencies:

  * ctapipe v0.28
  * pyirf v0.13
  * eventio v2.0
  * ctapipe-io-zfits v0.4 [`!50 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/50>`__]


datapipe 0.2.1 (2025-06-27)
---------------------------

Maintenance
-----------

- Now ships with: ctapipe-0.26, pyirf-0.13, and eventio-1.16, ctapipe-io-zfits-0.3 [`!39 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/39>`__]

datapipe v0.2.0 (2025-06-25)
----------------------------

New Features
~~~~~~~~~~~~

- Add CWL workflows for two use cases:

  * UC-DPPS-130-1.9 (Optimize event selection )
  * UC-DPPS-130-1.6 (Compute an IRF)
  * added workflow to optimize cuts and compute an IRF at once, given an analysis name
    used as prefix for the output files. [`!31 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/31>`__]

- Added CWL workflow for UC-DPPS-130-1.8 (Merge). [`!33 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/33>`__]

- Added CWL workflow for UC-DPPS-130-1.4 (Apply Reconstruction Models) [`!36 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/36>`__]

- UC-DPPS-130-1.3 (Train) is verified by inspection [`!37 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/37>`__]


Maintenance
~~~~~~~~~~~

- - Update docker URL in the installation page of the documentation to point to the CTAO Harbor, where the image is deployed
  - Simplify the README so that it is appropriate for PyPI. [`!22 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/22>`__]

- Add auto-generated documentation for the DataPipe CWL workflows, including diagrams. This appears in the *Workflows* section of the Sphinx docs. [`!35 <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe/-/merge_requests/35>`__]

datapipe v0.1.0 (2025-04-17)
--------------------------------

This is the first release of the datapipe package.

New Features
~~~~~~~~~~~~

- CWL workflows covering UC-DPPS-130-1.2, 1.2.1, and 1.2.2
