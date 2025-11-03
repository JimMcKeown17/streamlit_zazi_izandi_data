TOOL_SCHEMAS = [
    {
      "type": "function",
      "function": {
        "name": "percentage_at_benchmark_2023",
        "description": "Calculate the percentage of children meeting grade level benchmarks for 2023 data. Grade R benchmark is 20+ on EGRA, Grade 1 benchmark is 40+ on EGRA. Compares baseline vs endline performance.",
        "parameters": {
          "type": "object",
          "properties": {
            "grade": {
              "type": "string",
              "description": "Grade level to analyze",
              "enum": ["Grade R", "Grade 1", "All Grades"],
              "default": "All Grades"
            },
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. Use 'All Schools' for combined analysis.",
              "default": "All Schools"
            },
            "top_n": {
              "type": "integer",
              "description": "Return top n performing schools (only applicable when school='All Schools')",
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing benchmark analysis results",
          "properties": {
            "grade": {"type": "string"},
            "school": {"type": "string"},
            "benchmark": {"type": "integer"},
            "baseline_above_benchmark_percent": {"type": "number"},
            "endline_above_benchmark_percent": {"type": "number"},
            "improvement": {"type": "number"},
            "total_students": {"type": "integer"},
            "top_schools": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "school": {"type": "string"},
                  "endline_above_benchmark_percent": {"type": "number"},
                  "total_students": {"type": "integer"}
                }
              }
            },
            "results_by_grade": {"type": "object"},
            "error": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "improvement_scores_2023",
        "description": "Calculate improvement scores for EGRA or Letters Known assessments for 2023 data. Shows baseline to endline improvement averages.",
        "parameters": {
          "type": "object",
          "properties": {
            "metric": {
              "type": "string",
              "description": "Which assessment metric to analyze",
              "enum": ["EGRA", "Letters"],
              "default": "EGRA"
            },
            "grade": {
              "type": "string",
              "description": "Grade level to analyze",
              "enum": ["Grade R", "Grade 1", "All Grades"],
              "default": "All Grades"
            },
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. Use 'All Schools' for combined analysis.",
              "default": "All Schools"
            },
            "top_n": {
              "type": "integer",
              "description": "Return top n improving schools (only applicable when school='All Schools')",
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing improvement analysis results",
          "properties": {
            "metric": {"type": "string"},
            "grade": {"type": "string"},
            "school": {"type": "string"},
            "baseline_average": {"type": "number"},
            "endline_average": {"type": "number"},
            "improvement_average": {"type": "number"},
            "total_students": {"type": "integer"},
            "top_schools": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "school": {"type": "string"},
                  "improvement_average": {"type": "number"},
                  "total_students": {"type": "integer"}
                }
              }
            },
            "error": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "total_scores_2023",
        "description": "Get total score statistics (average, median, max, min) for EGRA or Letters Known assessments for 2023 data. Can analyze baseline or endline assessments.",
        "parameters": {
          "type": "object",
          "properties": {
            "metric": {
              "type": "string",
              "description": "Which assessment metric to analyze",
              "enum": ["EGRA", "Letters"],
              "default": "EGRA"
            },
            "assessment": {
              "type": "string",
              "description": "Which assessment point to analyze",
              "enum": ["Baseline", "Endline"],
              "default": "Endline"
            },
            "grade": {
              "type": "string",
              "description": "Grade level to analyze",
              "enum": ["Grade R", "Grade 1", "All Grades"],
              "default": "All Grades"
            },
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. Use 'All Schools' for combined analysis.",
              "default": "All Schools"
            },
            "top_n": {
              "type": "integer",
              "description": "Return top n scoring schools (only applicable when school='All Schools')",
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing score statistics",
          "properties": {
            "metric": {"type": "string"},
            "assessment": {"type": "string"},
            "grade": {"type": "string"},
            "school": {"type": "string"},
            "average_score": {"type": "number"},
            "median_score": {"type": "number"},
            "max_score": {"type": "number"},
            "min_score": {"type": "number"},
            "total_students": {"type": "integer"},
            "top_schools": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "school": {"type": "string"},
                  "average_score": {"type": "number"},
                  "total_students": {"type": "integer"}
                }
              }
            },
            "error": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "percentage_at_benchmark_2024",
        "description": "Calculate the percentage of children meeting grade level benchmarks for 2024 data. Grade R benchmark is 20+ on EGRA, Grade 1 benchmark is 40+ on EGRA. Can analyze baseline, midline, or endline assessments.",
        "parameters": {
          "type": "object",
          "properties": {
            "grade": {
              "type": "string",
              "description": "Grade level to analyze",
              "enum": ["Grade R", "Grade 1", "All Grades"],
              "default": "All Grades"
            },
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. Use 'All Schools' for combined analysis.",
              "default": "All Schools"
            },
            "assessment": {
              "type": "string",
              "description": "Assessment period to analyze",
              "enum": ["Baseline", "Midline", "Endline"],
              "default": "Endline"
            },
            "top_n": {
              "type": "integer",
              "description": "Return top n performing schools (only applicable when school='All Schools')",
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing benchmark analysis results",
          "properties": {
            "grade": {"type": "string"},
            "school": {"type": "string"},
            "assessment": {"type": "string"},
            "benchmark": {"type": "integer"},
            "baseline_above_benchmark_percent": {"type": "number"},
            "endline_above_benchmark_percent": {"type": "number"},
            "midline_above_benchmark_percent": {"type": "number"},
            "improvement": {"type": "number"},
            "total_students": {"type": "integer"},
            "top_schools": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "school": {"type": "string"},
                  "endline_above_benchmark_percent": {"type": "number"},
                  "midline_above_benchmark_percent": {"type": "number"},
                  "total_students": {"type": "integer"}
                }
              }
            },
            "results_by_grade": {"type": "object"},
            "error": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "improvement_scores_2024",
        "description": "Calculate improvement scores for EGRA or Letters Known assessments for 2024 data. Shows baseline to midline or endline improvement averages.",
        "parameters": {
          "type": "object",
          "properties": {
            "metric": {
              "type": "string",
              "description": "Which assessment metric to analyze",
              "enum": ["EGRA", "Letters"],
              "default": "EGRA"
            },
            "grade": {
              "type": "string",
              "description": "Grade level to analyze",
              "enum": ["Grade R", "Grade 1", "All Grades"],
              "default": "All Grades"
            },
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. Use 'All Schools' for combined analysis.",
              "default": "All Schools"
            },
            "assessment": {
              "type": "string",
              "description": "Target assessment period for improvement calculation",
              "enum": ["Midline", "Endline"],
              "default": "Endline"
            },
            "top_n": {
              "type": "integer",
              "description": "Return top n improving schools (only applicable when school='All Schools')",
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing improvement analysis results",
          "properties": {
            "metric": {"type": "string"},
            "grade": {"type": "string"},
            "school": {"type": "string"},
            "assessment": {"type": "string"},
            "baseline_average": {"type": "number"},
            "midline_average": {"type": "number"},
            "endline_average": {"type": "number"},
            "improvement_average": {"type": "number"},
            "total_students": {"type": "integer"},
            "top_schools": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "school": {"type": "string"},
                  "improvement_average": {"type": "number"},
                  "total_students": {"type": "integer"}
                }
              }
            },
            "error": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "total_scores_2024",
        "description": "Get total score statistics (average, median, max, min) for EGRA or Letters Known assessments for 2024 data. Can analyze baseline, midline, or endline assessments.",
        "parameters": {
          "type": "object",
          "properties": {
            "metric": {
              "type": "string",
              "description": "Which assessment metric to analyze",
              "enum": ["EGRA", "Letters"],
              "default": "EGRA"
            },
            "assessment": {
              "type": "string",
              "description": "Which assessment point to analyze",
              "enum": ["Baseline", "Midline", "Endline"],
              "default": "Endline"
            },
            "grade": {
              "type": "string",
              "description": "Grade level to analyze",
              "enum": ["Grade R", "Grade 1", "All Grades"],
              "default": "All Grades"
            },
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. Use 'All Schools' for combined analysis.",
              "default": "All Schools"
            },
            "top_n": {
              "type": "integer",
              "description": "Return top n scoring schools (only applicable when school='All Schools')",
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing score statistics",
          "properties": {
            "metric": {"type": "string"},
            "assessment": {"type": "string"},
            "grade": {"type": "string"},
            "school": {"type": "string"},
            "average_score": {"type": "number"},
            "median_score": {"type": "number"},
            "max_score": {"type": "number"},
            "min_score": {"type": "number"},
            "total_students": {"type": "integer"},
            "top_schools": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "school": {"type": "string"},
                  "average_score": {"type": "number"},
                  "total_students": {"type": "integer"}
                }
              }
            },
            "error": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "percentage_at_benchmark_2025",
        "description": "Calculate the percentage of children meeting grade level benchmarks for 2025 data. Grade R benchmark is 20+ letters, Grade 1 benchmark is 40+ letters. Compares initial vs midline performance.",
        "parameters": {
          "type": "object",
          "properties": {
            "grade": {
              "type": "string",
              "description": "Grade level to analyze",
              "enum": ["Grade R", "Grade 1", "All Grades"],
              "default": "All Grades"
            },
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. Use 'All Schools' for combined analysis.",
              "default": "All Schools"
            },
            "assessment": {
              "type": "string",
              "description": "Assessment period to analyze",
              "enum": ["Initial", "Midline"],
              "default": "Midline"
            },
            "top_n": {
              "type": "integer",
              "description": "Return top n performing schools (only applicable when school='All Schools')",
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing benchmark analysis results",
          "properties": {
            "grade": {"type": "string"},
            "school": {"type": "string"},
            "assessment": {"type": "string"},
            "benchmark": {"type": "integer"},
            "initial_above_benchmark_percent": {"type": "number"},
            "midline_above_benchmark_percent": {"type": "number"},
            "improvement": {"type": "number"},
            "total_students": {"type": "integer"},
            "top_schools": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "school": {"type": "string"},
                  "initial_above_benchmark_percent": {"type": "number"},
                  "midline_above_benchmark_percent": {"type": "number"},
                  "total_students": {"type": "integer"}
                }
              }
            },
            "results_by_grade": {"type": "object"},
            "error": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "improvement_scores_2025",
        "description": "Calculate improvement scores from initial to midline assessments for 2025 data. Shows initial to midline improvement averages for letter knowledge.",
        "parameters": {
          "type": "object",
          "properties": {
            "grade": {
              "type": "string",
              "description": "Grade level to analyze",
              "enum": ["Grade R", "Grade 1", "All Grades"],
              "default": "All Grades"
            },
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. Use 'All Schools' for combined analysis.",
              "default": "All Schools"
            },
            "top_n": {
              "type": "integer",
              "description": "Return top n improving schools (only applicable when school='All Schools')",
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing improvement analysis results",
          "properties": {
            "grade": {"type": "string"},
            "school": {"type": "string"},
            "initial_average": {"type": "number"},
            "midline_average": {"type": "number"},
            "improvement_average": {"type": "number"},
            "initial_total_students": {"type": "integer"},
            "midline_total_students": {"type": "integer"},
            "top_schools": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "school": {"type": "string"},
                  "improvement_average": {"type": "number"},
                  "midline_students": {"type": "integer"},
                  "initial_students": {"type": "integer"}
                }
              }
            },
            "error": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "total_scores_2025",
        "description": "Get total score statistics (average, median, max, min) for letter assessments for 2025 data. Can analyze initial or midline assessments.",
        "parameters": {
          "type": "object",
          "properties": {
            "assessment": {
              "type": "string",
              "description": "Which assessment point to analyze",
              "enum": ["Initial", "Midline"],
              "default": "Midline"
            },
            "grade": {
              "type": "string",
              "description": "Grade level to analyze",
              "enum": ["Grade R", "Grade 1", "All Grades"],
              "default": "All Grades"
            },
            "school": {
              "type": "string",
              "description": "Name of the school to analyze. Must match exactly with school names in the database. Use 'All Schools' for combined analysis.",
              "default": "All Schools"
            },
            "top_n": {
              "type": "integer",
              "description": "Return top n scoring schools (only applicable when school='All Schools')",
              "minimum": 1,
              "maximum": 50
            }
          },
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing score statistics",
          "properties": {
            "assessment": {"type": "string"},
            "grade": {"type": "string"},
            "school": {"type": "string"},
            "average_score": {"type": "number"},
            "median_score": {"type": "number"},
            "max_score": {"type": "number"},
            "min_score": {"type": "number"},
            "total_students": {"type": "integer"},
            "top_schools": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "school": {"type": "string"},
                  "average_score": {"type": "number"},
                  "total_students": {"type": "integer"}
                }
              }
            },
            "error": {"type": "string"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "program_summary_stats",
        "description": "Calculate comprehensive participation statistics for the Zazi iZandi program across all years (2023-2025). Provides total participants, unique schools, TAs, and participation patterns but excludes performance metrics.",
        "parameters": {
          "type": "object",
          "properties": {},
          "required": []
        },
        "returns": {
          "type": "object",
          "description": "Dictionary containing comprehensive program participation statistics across all years",
          "properties": {
            "program_totals": {
              "type": "object",
              "properties": {
                "total_children_across_all_years": {"type": "integer"},
                "grade_r_children_total": {"type": "integer"},
                "grade_1_children_total": {"type": "integer"},
                "unique_schools_across_all_years": {"type": "integer"},
                "unique_tas_across_all_years": {"type": "integer"},
                "children_per_school_average": {"type": "number"},
                "children_per_ta_average": {"type": "number"}
              }
            },
            "participation_by_grade": {
              "type": "object",
              "properties": {
                "schools_with_grade_r": {"type": "integer"},
                "schools_with_grade_1": {"type": "integer"},
                "schools_with_both_grades": {"type": "integer"}
              }
            },
            "multi_year_participation": {
              "type": "object",
              "properties": {
                "schools_in_multiple_years": {"type": "integer"},
                "tas_in_multiple_years": {"type": "integer"}
              }
            },
            "year_breakdown": {
              "type": "object",
              "description": "Statistics broken down by individual year",
              "additionalProperties": {
                "type": "object",
                "properties": {
                  "total_children": {"type": "integer"},
                  "grade_r_children": {"type": "integer"},
                  "grade_1_children": {"type": "integer"},
                  "unique_schools": {"type": "integer"},
                  "unique_tas": {"type": "integer"}
                }
              }
            },
            "years_covered": {
              "type": "array",
              "items": {"type": "string"},
              "description": "List of years included in the analysis"
            },
            "error": {"type": "string"}
          }
        }
      }
    }
  ]
