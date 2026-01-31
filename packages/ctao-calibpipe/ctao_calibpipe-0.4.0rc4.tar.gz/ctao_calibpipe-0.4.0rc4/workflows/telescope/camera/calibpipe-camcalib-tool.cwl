#!/usr/bin/env cwl-runner

cwlVersion: v1.2

class: CommandLineTool

baseCommand: calibpipe-calculate-camcalib-coefficients
requirements:
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - entry: $(inputs.camcalib_tool_input)
        writable: true
label: Camera Calibration Tool
doc: >
    The calibpipe-calculate-camcalib-coefficients tool is a command line tool that calculates the camera calibration
    coefficients for the camera pixels. It is part of the calibpipe software package and is used to process data from
    the Cherenkov Telescope Array Observatory (CTAO).

inputs:
  camcalib_tool_input:
    type: File
    inputBinding:
      prefix: --input_url
    label: DL1 monitoring
    doc: >
        DL1 monitoring data containing aggregated pixel-wise statistics,
        detected pixel outliers, and defined faulty data periods.

  configuration:
    type: ["null", File, string]
    default: null
    inputBinding:
      prefix: --config
    doc: >
        Optional configuration File or string as path.

  log-level:
    type: string?
    inputBinding:
      prefix: --log-level

  provenance_log_filename:
    type: string
    doc: file in which to write the local provenance.
    default: calibpipe-calculate-camcalib-coefficients.provenance.log
    inputBinding:
      prefix: --provenance-log

outputs:
  dl1_mon_data:
    type: File
    label: DL1 monitoring
    outputBinding:
      glob: $(inputs.camcalib_tool_input.basename)
  provenance_log:
    type: File
    label: Provenance log
    outputBinding:
      glob: $(inputs.provenance_log_filename)
