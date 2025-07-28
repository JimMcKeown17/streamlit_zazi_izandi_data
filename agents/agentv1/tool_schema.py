TOOL_SCHEMAS = [
    {
      "type": "function",
      "function": {
        "name": "grade1_benchmark_per_school",
        "description": "Calculate the percentage of Grade 1 children meeting the grade level benchmark for letter knowledge. Can analyze a specific school or all schools combined. Compares initial assessment (before April 15, 2025) vs midline assessment (after April 15, 2025) performance.",
        "parameters": {
          "type": "object",
          "properties": {
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. If not provided or null, calculates aggregated statistics for all schools combined.",
              "default": null
            },
            "benchmark": {
              "type": "integer",
              "description": "Letter knowledge benchmark threshold. Students with letters_correct >= this value are considered above grade level.",
              "default": 40,
              "minimum": 0,
              "maximum": 100
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing benchmark analysis results",
          "properties": {
            "school": {
              "type": "string",
              "description": "Name of the analyzed school or 'All Schools' if no specific school was provided"
            },
            "benchmark": {
              "type": "integer", 
              "description": "Benchmark threshold used for analysis"
            },
            "initial_above_benchmark_percent": {
              "type": "number",
              "description": "Percentage of Grade 1 students above benchmark in initial assessment (rounded to 1 decimal)"
            },
            "midline_above_benchmark_percent": {
              "type": "number",
              "description": "Percentage of Grade 1 students above benchmark in midline assessment (rounded to 1 decimal)"
            },
            "initial_total_students": {
              "type": "integer",
              "description": "Total number of Grade 1 students in initial assessment"
            },
            "midline_total_students": {
              "type": "integer", 
              "description": "Total number of Grade 1 students in midline assessment"
            },
            "improvement": {
              "type": "number",
              "description": "Percentage point improvement from initial to midline (midline - initial)"
            },
            "schools_in_initial": {
              "type": "integer",
              "description": "Number of unique schools represented in initial assessment (only present when analyzing all schools)"
            },
            "schools_in_midline": {
              "type": "integer",
              "description": "Number of unique schools represented in midline assessment (only present when analyzing all schools)"
            },
            "error": {
              "type": "string",
              "description": "Error message if no Grade 1 data found (optional field)"
            }
          }
        }
      }
    }
  ]
