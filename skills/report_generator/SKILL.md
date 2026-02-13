# Report Generator Skill

## Purpose
Generate professional reports from data sources.

## Parameters
- `report_type`: Type of report to generate. One of: `sales`, `analytics`, `performance`.
- `period`: Time period for the report. Examples: `Q1`, `Q2`, `Q3`, `Q4`, or a year like `2024`.
- `data_source`: (optional) Path to a data file to use as input.

## Output
Returns a dict with:
- `status`: `"success"` or `"error"`
- `report_path`: Path to the generated report file
- `summary`: Dict containing key metrics from the report
