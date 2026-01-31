#!/usr/bin/env cwl-runner

cwlVersion: v1.2

class: Workflow
requirements:
  InlineJavascriptRequirement: {}
  StepInputExpressionRequirement: {}
  ScatterFeatureRequirement: {}
  MultipleInputFeatureRequirement: {}

label: Optical throughput measurements via muon ring analysis
doc: >
    Upon receiving a new DL0 data product (from either Monte Carlo simulations or observations), DPPS triggers the CalibPipe
    (ctapipe-process) to process the data using ctapipe, extracting the signal charges and reconstructing muon parameters.
    The second step involves using the CalibPipe tool to estimate the telescope’s optical throughput using a
    predefined number of muon events.

inputs:
  dl0_input_data:
    type: File[]
    label: DL0 file with pre-tagged muon events
    doc: >
        DL0 data/simulation with pre-tagged muon events for optical throughput measurements.
  output_filename:
    type: string
    label: Output filename
    doc: >
      DL1/monitoring file name for the output data product containing the optical throughput table.
  process_config:
    type: File[]
    label: Muon image process
    doc: >
        Configuration file for Muon image process.
  merge_config:
    type: File?
    label: Merge config
    doc: >
      Configuration file for merging ctapipe HDF5 files.
  throughput_muon_config:
    type: File
    label: Muon optical throughput calculator config
    doc: >
        Configuration file for Muon optical throughput calibration
  log-level:
    type: string?
    doc: >
        Log level for the process. Default is INFO.
  provenance_log_filename:
    type: string
    label: Provenance log filename
    doc: >
      Name of the file in which to write the local provenance.
    default: optical_throughput.provenance.log

outputs:
  dl1_muon_throughput_data:
    type: File
    label: DL1 with optical throughput
    doc: >
        Aggregated muon statistics (observation or simulation) for optical throughput estimation.
    outputSource: calculate_throughput/dl1_data_with_throughput
  provenance_log:
    type: File
    label: Provenance log
    outputSource: calculate_throughput/provenance_log

steps:
  process_muon_image:
    run: ../ctapipe-process-tool.cwl
    in:
      process_tool_input: dl0_input_data
      process_tool_output:
        valueFrom: $(inputs.process_tool_input.basename.replace(/(?<!\d)\..*$/, '') + '.dl1.h5')
      configuration: process_config
      log-level: log-level
    scatter: process_tool_input
    scatterMethod: "dotproduct"
    out: [dl1_data]
  merge_muon_image:
    run: ../ctapipe-merge-tool.cwl
    when: $(inputs.input_files.length > 1)
    in:
      input_files: process_muon_image/dl1_data
      configuration: merge_config
      output_filename: output_filename
    out: [merged_output]
  rename_single_muon:
    run: ../../utils/copy-file.cwl
    when: $(inputs.input_files.length === 1)
    in:
      input_files:
        source: process_muon_image/dl1_data
      output_filename: output_filename
    out: [copied_file]
  calculate_throughput:
    run: calibpipe-throughput-muon-tool.cwl
    in:
      muon_throughput_tool_input:
        source:
          - merge_muon_image/merged_output
          - rename_single_muon/copied_file
        pickValue: first_non_null
      configuration: throughput_muon_config
      log-level: log-level
      provenance_log_filename: provenance_log_filename
    out:
      - dl1_data_with_throughput
      - provenance_log
