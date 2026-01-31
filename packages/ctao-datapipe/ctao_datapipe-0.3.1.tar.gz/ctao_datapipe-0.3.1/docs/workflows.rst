=========
Workflows
=========

.. contents::

Event Processing
================

.. cwl_workflow_graph:: ../workflows/workflow_dl0_to_dl2.cwl
.. cwl_workflow:: ../workflows/process_dl0_dl1.cwl
..
   cwl_workflow:: ../workflows/process_dl0_dl1_multiple.cwl
.. cwl_workflow:: ../workflows/process_dl1_dl2.cwl
.. cwl_workflow:: ../workflows/workflow_dl0_to_dl2.cwl


Reconstruction Model Training
=============================

.. cwl_workflow:: ../workflows/train_energy_model.cwl
.. cwl_workflow:: ../workflows/train_gammaness_model.cwl
.. cwl_workflow:: ../workflows/train_disp_model.cwl

Event File Operations
=====================

.. cwl_workflow:: ../workflows/merge.cwl
.. cwl_workflow:: ../workflows/apply_models.cwl

Cut optimization and IRF production
===================================

.. cwl_workflow_graph:: ../workflows/workflow_optimize_and_irf.cwl
.. cwl_workflow:: ../workflows/workflow_optimize_and_irf.cwl
.. cwl_workflow:: ../workflows/optimize.cwl
.. cwl_workflow:: ../workflows/compute_irf.cwl
