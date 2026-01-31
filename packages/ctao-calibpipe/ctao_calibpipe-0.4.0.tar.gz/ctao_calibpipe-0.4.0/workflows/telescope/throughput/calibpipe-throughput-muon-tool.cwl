#!/usr/bin/env cwl-runner

cwlVersion: v1.2

class: CommandLineTool

baseCommand: calibpipe-calculate-throughput-muon
requirements:
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - entry: $(inputs.muon_throughput_tool_input)
        writable: true

label: Muon Throughput Calibration Tool
doc: >
    The calibpipe-calculate-throughput-muon is a command line tool that calculates the optical
    throughput via muon rings analysis. It is part of the calibpipe software package and is used to
    process data from the Cherenkov Telescope Array Observatory (CTAO).

inputs:
  muon_throughput_tool_input:
    type: File
    inputBinding:
      prefix: --input
    label: DL1 data with reconstructed muons.
    doc: >
        DL1 data/file containing reconstructed muon events, with a table filled with MuonParametersContainer data for each event.
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
    doc: >
        Log level for the process. Default is INFO.
  provenance_log_filename:
    type: string
    doc: file in which to write the local provenance.
    default: calibpipe-calculate-throughput-muon.provenance.log
    inputBinding:
      prefix: --provenance-log

outputs:
  dl1_data_with_throughput:
    type: File
    label: DL1 file includes a throughput monitoring table and the corresponding associated errors.
    outputBinding:
      glob: $(inputs.muon_throughput_tool_input.basename)
  provenance_log:
    type: File
    label: Provenance log
    outputBinding:
      glob: $(inputs.provenance_log_filename)
