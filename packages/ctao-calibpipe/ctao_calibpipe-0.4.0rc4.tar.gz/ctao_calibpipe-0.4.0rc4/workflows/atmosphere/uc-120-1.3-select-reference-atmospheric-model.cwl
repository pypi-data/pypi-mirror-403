#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

label: Select Reference Atmospheric Model

doc: >
  This tool implements UC-120.1.3. It selects a reference atmospheric model based on the provided
  configuration files. It generates an atmospheric profile and a Rayleigh
  extinction table as outputs. The `--config` input specifies the configuration
  files, and the optional `--log-level` input sets the logging verbosity.
  Credentials for accessing required resources (GDAS meteorological data)
  are provided via the `credentials` input.

requirements:
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
    - $(inputs.credentials)

inputs:
  configuration:
    type:
      type: array
      items: File
      inputBinding:
        prefix: --config
  credentials:
    type: File
  log-level:
    type: string?
    inputBinding:
      prefix: --log-level
  provenance_log_filename:
    type: string
    label: Provenance log filename
    doc: >
      Name of the file in which to write the local provenance.
    default: calibpipe-select-reference-atmospheric-model.provenance.log
    inputBinding:
      prefix: --provenance-log

outputs:
  atmospheric_profile:
    type: File
    outputBinding:
      glob: selected_atmospheric_profile.ascii.ecsv
  rayleigh_extinction_table:
    type: File
    outputBinding:
      glob: selected_rayleigh_extinction_profile.ascii.ecsv
  provenance_log:
    type: File
    label: Provenance log
    outputBinding:
      glob: $(inputs.provenance_log_filename)

baseCommand: calibpipe-select-reference-atmospheric-model

temporaryFailCodes: [100]
