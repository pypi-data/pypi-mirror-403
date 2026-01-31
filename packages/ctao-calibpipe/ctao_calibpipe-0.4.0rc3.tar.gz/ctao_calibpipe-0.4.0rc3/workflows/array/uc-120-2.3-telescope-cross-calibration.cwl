#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool
baseCommand:
  - calibpipe-cross-calibration
requirements:
  InlineJavascriptRequirement: {}
label: Perform telescope cross calibration
doc: |
  This tool implements UC-120-2.3. It performs array cross calibration. The
  `--config` input specifies the configuration file for the tool, and the
  optional `--log-level` input sets the logging verbosity. The output is used
  in atmospheric modeling workflows.

inputs:

  cross_calibration_tool_input:
    type: File
    inputBinding:
      prefix: --input_url
    label: DL2 data

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
    doc: file in which to write the local ctapipe-process provenance.
    default: cross-calibration.provenance.log
    inputBinding:
      prefix: --provenance-log

  output_filename:
    type: string
    inputBinding:
      prefix: --output_url
    label: DL2 data

outputs:

  dl2_data:
    type: File
    outputBinding:
      glob: $(inputs.output_filename)

  provenance_log:
    type: File
    doc: ctapipe format provenance log for this step.
    outputBinding:
      glob: $(inputs.provenance_log_filename)
