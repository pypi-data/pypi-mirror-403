#!/usr/bin/env cwl-runner

cwlVersion: v1.2

class: CommandLineTool
label: Merge Monitoring Files
baseCommand: ctapipe-merge
requirements:
  InlineJavascriptRequirement: {}
doc: |
  Merge multiple monitoring HDF5 files into a single output file using ctapipe-merge.

inputs:
  output_filename:
    type: string
    doc: name of the output filename
    inputBinding:
      position: 1
      prefix: --output

  same_ob:
    type: boolean
    default: false
    inputBinding:
      position: 2
      prefix: --single-ob

  attach_monitoring:
    type: boolean
    default: false
    inputBinding:
      position: 3
      prefix: --attach-monitoring

  configuration:
    type: File?
    inputBinding:
      position: 4
      prefix: --config
    doc: The configuration file for ctapipe-merge

  provenance_log_filename:
    type: string
    doc: file in which to write the local provenance.
    default: ctapipe-merge.provenance.log
    inputBinding:
      position: 5
      prefix: --provenance-log

  input_files:
    type: File[]
    doc: |
      Paths to monitoring files to be merged into output_filename
    inputBinding:
      position: 6

  log-level:
    type: string?
    inputBinding:
      position: 7
      prefix: --log-level

outputs:
  merged_output:
    type: File
    doc: output file.
    outputBinding:
      glob: $(inputs.output_filename)
  provenance_log:
    type: File
    label: Provenance log
    outputBinding:
      glob: $(inputs.provenance_log_filename)
