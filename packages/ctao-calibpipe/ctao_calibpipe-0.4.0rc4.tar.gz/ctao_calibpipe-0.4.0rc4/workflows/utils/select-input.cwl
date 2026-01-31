class: ExpressionTool
cwlVersion: v1.2

requirements:
  InlineJavascriptRequirement: {}

doc: "Return merged file if available, otherwise the first scattered file."

inputs:
  merged:
    type: File?
  scattered:
    type: File[]

outputs:
  selected:
    type: File

expression: |
  ${
    // Prefer merged if it exists
    if (inputs.merged != null) {
      return { selected: inputs.merged };
    }

    // Fall back to first scattered file (must exist)
    if (inputs.scattered && inputs.scattered.length > 0) {
      return { selected: inputs.scattered[0] };
    }

    throw new Error("Neither merged nor scattered inputs provided");
  }
