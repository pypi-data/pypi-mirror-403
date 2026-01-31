#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

label: Create Contemporary Atmospheric Model

doc: >
  This tool implements UC-120-1.7. It creates a contemporary atmospheric model by combining the provided
  configuration files and a 12-month average CO2 background concentration
  (12-MACOBAC) table. It generates an atmospheric profile and a Rayleigh
  extinction table as outputs. The `--config` input specifies the configuration
  files, the `--macobac12-table-path` input provides the path to the 12-MACOBAC
  table, and the optional `--log-level` input sets the logging verbosity.
  Credentials for accessing required resources (GDAS or ECMWF meteorological data)
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
    default: calibpipe-create-molecular-atmospheric-model.provenance.log
    inputBinding:
      prefix: --provenance-log
  macobac_table:
    type: File
    inputBinding:
      prefix: --macobac12-table-path

outputs:
  atmospheric_profile:
    type: File
    outputBinding:
      glob: contemporary_atmospheric_profile.ascii.ecsv
  rayleigh_extinction_table:
    type: File
    outputBinding:
      glob: contemporary_rayleigh_extinction_profile.ascii.ecsv
  provenance_log:
    type: File
    label: Provenance log
    outputBinding:
      glob: $(inputs.provenance_log_filename)

baseCommand: calibpipe-create-molecular-atmospheric-model

temporaryFailCodes: [100]
