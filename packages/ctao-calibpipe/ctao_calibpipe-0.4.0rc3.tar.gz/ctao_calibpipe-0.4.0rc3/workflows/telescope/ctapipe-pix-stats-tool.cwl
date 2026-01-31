#!/usr/bin/env cwl-runner

cwlVersion: v1.2

class: CommandLineTool

baseCommand: ctapipe-calculate-pixel-statistics
requirements:
  InlineJavascriptRequirement: {}
label: Pixel Statistics Tool
doc: >
    The ctapipe-calculate-pixel-statistics tool is a command line tool that calculates pixel-wise statistics from DL1
    data. It is part of the ctapipe software package and is used to process data from the Cherenkov Telescope Array
    Observatory (CTAO).

inputs:
  pix_stats_tool_input:
    type: File
    inputBinding:
      prefix: --input_url
    label: DL1
    doc: >
        DL1 data file including images.

  pix_stats_tool_output:
    type: [File, string]
    inputBinding:
      prefix: --output_path
    label: DL1 monitoring
    doc: >
        DL1 monitoring data containing aggregated pixel-wise statistics,
        detected pixel outliers, and defined faulty data periods.

  configuration:
    type: File
    inputBinding:
      prefix: --config

  log-level:
    type: string?
    inputBinding:
      prefix: --log-level

  provenance_log_filename:
    type: string
    doc: file in which to write the local provenance.
    default: ctapipe-calculate-pixel-statistics.provenance.log
    inputBinding:
      prefix: --provenance-log

outputs:
  stats_agg_data:
    type: File
    outputBinding:
      glob: $(inputs.pix_stats_tool_output)
  provenance_log:
    type: File
    label: Provenance log
    outputBinding:
      glob: $(inputs.provenance_log_filename)
