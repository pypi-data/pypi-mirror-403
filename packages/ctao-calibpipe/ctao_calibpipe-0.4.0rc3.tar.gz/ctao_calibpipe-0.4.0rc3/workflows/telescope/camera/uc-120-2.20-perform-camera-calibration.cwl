#!/usr/bin/env cwl-runner

cwlVersion: v1.2

class: Workflow
requirements:
  InlineJavascriptRequirement: {}
  StepInputExpressionRequirement: {}
  ScatterFeatureRequirement: {}
  MultipleInputFeatureRequirement: {}

label: Perform camera calibration
doc: >
  When DPPS receives a new DL0 data product, the CalibPipe is triggered to process the calibration events. The CalibPipe performs charge integration and peak time extraction for the entire set of calibration events, and computes aggregated time-series statistics, including the mean, median, and standard deviation.
  Using these aggregated statistics, the CalibPipe identifies faulty camera pixels, such as those affected by starlight, by applying various outlier detection criteria. Time periods with a significant number of faulty pixels, exceeding a predefined threshold, are flagged as invalid. A refined treatment can then be applied to these time periods to account for the issues.
  Following this, pixel- and channel-wise camera calibration coefficients including the sky pedestal offsets per waveform sample, flat-fielding coefficients, and pixel timing corrections are calculated as a function of time.
  The workflow automatically merges DL1 outputs when multiple DL0 files are provided and skips merging when only one file is given.
inputs:
  dl0_pedestal_data:
    type: File[]
    label: Pedestal DL0 files
    doc: >
      DL0 data files containing pedestal calibration events.
  dl0_flatfield_data:
    type: File[]
    label: Flat-field DL0 files
    doc: >
      DL0 data files containing flat-field calibration events.
  ped_process_config:
    type: File[]
    label: Pedestal process config
    doc: >
      Configuration file for pedestal event processing.
  ff_process_config:
    type: File[]
    label: Flat-field process config
    doc: >
      Configuration file for flat-field event processing.
  ped_img_pix_stats_config:
    type: File
    label: Pedestal pixel stats config
    doc: >
      Configuration file for the pixel statistics extraction of the charge for pedestal events.
  ff_img_pix_stats_config:
    type: File
    label: Flat-field pixel stats config
    doc: >
      Configuration file for the pixel statistics extraction of the charge for flat-field events.
  ff_time_pix_stats_config:
    type: File
    label: Peak time pixel stats config
    doc: >
      Configuration file for the pixel statistics extraction of the peak arrival time for flat-field events.
  merge_config:
    type: File?
    label: Merge config
    doc: >
      Configuration file for merging ctapipe HDF5 files.
  coeffs_camcalib_config:
    type: File
    label: Camera calibration coefficients config
    doc: >
      Configuration file for the camera calibration coefficient computation tool.
  output_filename:
    type: string
    label: Output filename
    doc: >
      DL1/monitoring file name for the output data product containing the camera calibration coefficients.
    default: camera_calibration.mon.dl1.h5
  provenance_log_filename:
    type: string
    label: Provenance log filename
    doc: >
      Name of the file in which to write the local provenance.
    default: camera_calibration.provenance.log

outputs:
  camcalib_dl1_mon_data:
    type: File
    label: DL1 monitoring data with camera calibration coefficients
    outputSource: camcalib_coeffs/dl1_mon_data
  provenance_log:
    type: File
    label: Provenance log
    outputSource: camcalib_coeffs/provenance_log

steps:
  process_pedestal:
    run: ../ctapipe-process-tool.cwl
    in:
      process_tool_input: dl0_pedestal_data
      process_tool_output:
        valueFrom: $(inputs.process_tool_input.basename.replace(/\..*$/, '') + '.dl1.h5')
      configuration: ped_process_config
    scatter: process_tool_input
    scatterMethod: "dotproduct"
    out: [dl1_data]

  process_flatfield:
    run: ../ctapipe-process-tool.cwl
    in:
      process_tool_input: dl0_flatfield_data
      process_tool_output:
        valueFrom: $(inputs.process_tool_input.basename.replace(/\..*$/, '') + '.dl1.h5')
      configuration: ff_process_config
    scatter: process_tool_input
    scatterMethod: "dotproduct"
    out: [dl1_data]

  merge_pedestal_dl1:
    run: ../ctapipe-merge-tool.cwl
    when: $(inputs.input_files.length > 1)
    in:
      input_files: process_pedestal/dl1_data
      same_ob:
        valueFrom: $(true)
      attach_monitoring:
        valueFrom: $(false)
      configuration: merge_config
      output_filename:
        valueFrom: "pedestal_all.merged.dl1.h5"
    out: [merged_output]

  merge_flatfield_dl1:
    run: ../ctapipe-merge-tool.cwl
    when: $(inputs.input_files.length > 1)
    in:
      input_files: process_flatfield/dl1_data
      same_ob:
        valueFrom: $(true)
      attach_monitoring:
        valueFrom: $(false)
      configuration: merge_config
      output_filename:
        valueFrom: "flatfield_all.merged.dl1.h5"
    out: [merged_output]

  select_pedestal_input:
    run: ../../utils/select-input.cwl
    in:
      merged: merge_pedestal_dl1/merged_output
      scattered: process_pedestal/dl1_data
    out: [selected]

  agg_stats_pedestal:
    run: ../ctapipe-pix-stats-tool.cwl
    in:
      pix_stats_tool_input: select_pedestal_input/selected
      configuration: ped_img_pix_stats_config
      pix_stats_tool_output:
        valueFrom: "pix_stats_pedestal_image.monitoring.dl1.h5"
    out: [stats_agg_data]

  select_flatfield_input:
    run: ../../utils/select-input.cwl
    in:
      merged: merge_flatfield_dl1/merged_output
      scattered: process_flatfield/dl1_data
    out: [selected]

  agg_stats_flatfield:
    run: ../ctapipe-pix-stats-tool.cwl
    in:
      pix_stats_tool_input: select_flatfield_input/selected
      configuration: ff_img_pix_stats_config
      pix_stats_tool_output:
        valueFrom: "pix_stats_flatfield_image.monitoring.dl1.h5"
    out: [stats_agg_data]

  agg_stats_time:
    run: ../ctapipe-pix-stats-tool.cwl
    in:
      pix_stats_tool_input: select_flatfield_input/selected
      configuration: ff_time_pix_stats_config
      pix_stats_tool_output:
        valueFrom: "pix_stats_flatfield_time.monitoring.dl1.h5"
    out: [stats_agg_data]

  agg_stats_merged:
    run: ../ctapipe-merge-tool.cwl
    in:
      input_files:
        - agg_stats_pedestal/stats_agg_data
        - agg_stats_flatfield/stats_agg_data
        - agg_stats_time/stats_agg_data
      same_ob:
        valueFrom: $(false)
      attach_monitoring:
        valueFrom: $(true)
      configuration: merge_config
      output_filename: output_filename
    out: [merged_output]

  camcalib_coeffs:
    run: ./calibpipe-camcalib-tool.cwl
    in:
      camcalib_tool_input: agg_stats_merged/merged_output
      configuration: coeffs_camcalib_config
      provenance_log_filename: provenance_log_filename
    out:
      - dl1_mon_data
      - provenance_log
