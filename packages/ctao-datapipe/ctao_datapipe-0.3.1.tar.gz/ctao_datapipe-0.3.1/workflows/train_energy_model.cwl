%YAML 1.1
---
cwlVersion: v1.2
class: CommandLineTool
baseCommand: ctapipe-train-energy-regressor
label: Train Energy Reconstruction Model
doc: |
  Train an energy reconstruction model that can predict :math:`E_{reco}` from DL1 and
  DL2 input parameters using gamma simulations.

inputs:
  config:
    type: File
    inputBinding:
      prefix: --config
    doc: |
      Sets the parameters for the ctapipe-train-energy-model tool.
  gamma_events:
    type: File
    doc: simulated gamma-ray events with known energies to train on.
    inputBinding:
      prefix: --input
  output_filename:
    type: string
    doc: filename of output energy reconstruction model, in PKL format.
    default: energy_reco_model.pkl
    inputBinding:
      prefix: --output
  provenance_log_filename:
    type: string
    doc: file in which to write the local provenance.
    default: train_energy_model.provenance.log
    inputBinding:
      prefix: --provenance-log
  cv_output_filename:
    type: string?
    doc: filename for output cross-validation file, in HDF5 format
    default: energy_cross_validation.h5
    inputBinding:
      prefix: --cv-output

outputs:
  reco_model:
    type: File
    doc: energy reconstruction model, in PKL format.
    outputBinding:
      glob: $(inputs.output_filename)
  cross_validation:
    type: File?
    doc: Cross-validation output for the model
    outputBinding:
        glob: $(inputs.cv_output_filename)
  provenance_log:
    type: File
    doc: ctapipe-format provenance log for this step
    outputBinding:
      glob: $(inputs.provenance_log_filename)
