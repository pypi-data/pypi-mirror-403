%YAML 1.1
---
cwlVersion: v1.2
class: CommandLineTool
baseCommand: ctapipe-train-particle-classifier
label: Train Gammaness Reconstruction Model
doc: |
  Train an reconstruction model that can predict a *gammaness* parameter to
  discriminate gamma from cosmic-ray events from DL1 and DL2 input parameters
  using gamma (signal) and proton/electron (background) simulations.

inputs:
  config:
    type: File
    inputBinding:
      prefix: --config
    doc: |
      Sets the parameters for the ctapipe-train-particle-classifier tool.
  gamma_events:
    type: File
    doc: input signal events, which should be gamma-ray simulations. Should be processed to
         DL2 with reconstructed energy included, if used as in input parameter in the config.
    inputBinding:
      prefix: --signal
  background_events:
    type: File
    doc: |
         input background events, which should be proton or a combination of
         proton and electron simulations or real observations that have been reconstructed up to DL2 with reconstructed energy.
    inputBinding:
      prefix: --background

  output_filename:
    type: string
    doc: filename of output gammaness reconstruction model, in PKL format.
    default: gammaness_reco_model.pkl
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
    default: gammaness_cross_validation.h5
    inputBinding:
      prefix: --cv-output

outputs:
  reco_model:
    type: File
    doc: gammaness reconstruction model, in PKL format.
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
