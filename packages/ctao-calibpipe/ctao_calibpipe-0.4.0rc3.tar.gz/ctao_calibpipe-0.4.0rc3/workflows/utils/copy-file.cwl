cwlVersion: v1.2
class: CommandLineTool
inputs:
  input_files: File[]
  output_filename: string
outputs:
  copied_file:
    type: File
    outputBinding:
      glob: $(inputs.output_filename)
baseCommand: ["cp"]
arguments:
  - $(inputs.input_files[0].path)
  - $(inputs.output_filename)
