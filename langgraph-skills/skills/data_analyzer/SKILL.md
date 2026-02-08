# Data Analyzer Skill

## Purpose
Analyze a dataset and produce statistical summaries, detect anomalies, and provide insights.

## Parameters
- `dataset`: Name or identifier of the dataset to analyze.
- `analysis_type`: Type of analysis to perform. One of: `summary`, `anomaly_detection`, `correlation`.
- `columns`: (optional) List of column names to focus the analysis on.

## Output
Returns a dict with:
- `status`: `"success"` or `"error"`
- `analysis_type`: The type of analysis performed
- `results`: Dict containing the analysis output
