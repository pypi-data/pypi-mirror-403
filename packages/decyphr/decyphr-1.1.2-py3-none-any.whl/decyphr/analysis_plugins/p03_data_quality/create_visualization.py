# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p03_data_quality/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Data Quality, visualizing 12 key features
#          using the Antigravity design system.

from typing import Dict, Any, Optional, List

# --- Helper Functions (Antigravity Design System) ---

def _create_card(title: str, content: str, subtitle: str = "") -> str:
    """Wraps content in a standard Antigravity details-card."""
    if not content: return ""
    sub = f"<p style='color: var(--text-tertiary); font-size: 0.9em; margin-top: -10px; margin-bottom: 20px;'>{subtitle}</p>" if subtitle else ""
    return f"""
    <div class='details-card'>
        <h3>{title}</h3>
        {sub}
        {content}
    </div>
    """

def _create_warning_card(title: str, items: List[str], icon: str = "⚠️") -> str:
    """Creates a styled warning card for critical issues."""
    if not items: return ""
    list_items = "".join([f"<li>{item}</li>" for item in items])
    return f"""
    <div style='background: var(--status-warning-bg); color: var(--status-warning-text); padding: 24px; border-radius: var(--radius-card); margin-bottom: 24px; border: 1px solid var(--status-warning-border, transparent);'>
        <h3 style='margin-bottom: 12px; font-weight: 600; display: flex; align-items: center; gap: 8px;'>{icon} {title}</h3>
        <ul style='padding-left: 20px; margin-bottom: 0; line-height: 1.6;'>
            {list_items}
        </ul>
    </div>
    """

def _create_table(headers: List[str], rows: List[List[Any]], overflow: bool = False) -> str:
    """Creates a standard transparent Antigravity table."""
    if not rows: return "<p style='color: var(--text-tertiary); font-style: italic;'>No issues found.</p>"
    
    thead = "".join([f"<th>{h}</th>" for h in headers])
    tbody = ""
    for row in rows:
        tbody += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    
    wrapper_class = "table-responsive" if overflow else ""
    return f"""
    <div class='{wrapper_class}'>
        <table class='details-table'>
            <thead><tr>{thead}</tr></thead>
            <tbody>{tbody}</tbody>
        </table>
    </div>
    """

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content to display data quality warnings and insights.
    """
    print("     -> Generating details for extended data quality issues...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}

    # --- Extract Results ---
    constant_cols = analysis_results.get("constant_columns", [])
    whitespace_issues = analysis_results.get("whitespace_issues", [])
    duplicate_rows = analysis_results.get("duplicate_rows", {})
    null_analysis = analysis_results.get("null_analysis", [])
    outliers = analysis_results.get("outliers", [])
    numeric_as_string = analysis_results.get("numeric_as_string", [])
    negative_values = analysis_results.get("negative_values", [])
    empty_strings = analysis_results.get("empty_strings", [])
    unique_candidates = analysis_results.get("unique_candidates", [])
    high_corr = analysis_results.get("high_correlation", [])
    high_card = analysis_results.get("high_cardinality", [])
    quasi_constant = analysis_results.get("quasi_constant", [])

    all_details_html: List[str] = []

    try:
        # --- 1. Critical Alerts (Duplicates & Constants) ---
        alerts = []
        if duplicate_rows.get("count", 0) > 0:
            alerts.append(f"<b>{duplicate_rows['count']:,} Duplicate Rows</b> detected ({duplicate_rows['percentage']}%) - Consider removing them.")
        if constant_cols:
            alerts.append(f"<b>{len(constant_cols)} Constant Columns</b>: {', '.join(constant_cols[:5])}{'...' if len(constant_cols)>5 else ''}")
        
        if alerts:
            all_details_html.append(_create_warning_card("Critical Data Issues", alerts))

        # --- 2. Nullity & Empty Strings ---
        # Combine into one section
        null_rows = [[x['column'], f"{x['count']:,}", f"{x['percentage']}%"] for x in null_analysis]
        empty_rows = [[x['column'], f"{x['count']:,}"] for x in empty_strings]
        
        null_content = _create_table(["Column", "Null Count", "% Missing"], null_rows)
        empty_content = _create_table(["Column", "Empty String Count"], empty_rows)
        
        if null_analysis or empty_strings:
            all_details_html.append(_create_card("Missing Data Analysis", 
                f"<div style='display: grid; grid-template-columns: 1fr 1fr; gap: 24px;'><div><h4>Null Values</h4>{null_content}</div><div><h4>Empty Strings</h4>{empty_content}</div></div>",
                "Deep dive into missingness and empty placeholders."))

        # --- 3. Outliers & Negative Values ---
        outlier_rows = [[x['column'], f"{x['count']:,}", f"{x['percentage']}%", f"{x['lower_limit']:.2f}", f"{x['upper_limit']:.2f}"] for x in outliers]
        neg_rows = [[x['column'], f"{x['count']:,}"] for x in negative_values]
        
        outlier_content = _create_table(["Column", "Outliers", "%", "Lower Bound", "Upper Bound"], outlier_rows, overflow=True)
        neg_content = _create_table(["Column", "Negative Count"], neg_rows)
        
        if outliers or negative_values:
            all_details_html.append(_create_card("Distribution Anomalies",
                 f"<div style='display: grid; grid-template-columns: 2fr 1fr; gap: 24px;'><div><h4>Outliers (IQR Method)</h4>{outlier_content}</div><div><h4>Negative Values</h4>{neg_content}</div></div>",
                 "Identifying statistical anomalies and potential valid-value range violations."))

        # --- 4. Data Type & Formatting Issues ---
        ws_rows = [[x['column'], f"{x['leading_spaces']:,}", f"{x['trailing_spaces']:,}"] for x in whitespace_issues]
        num_str_rows = [[x['column'], f"{x['match_percentage']}%"] for x in numeric_as_string]
        
        ws_content = _create_table(["Column", "Leading Spaces", "Trailing Spaces"], ws_rows)
        num_str_content = _create_table(["Column", "Numeric Match %"], num_str_rows)
        
        if whitespace_issues or numeric_as_string:
             all_details_html.append(_create_card("Formatting & Type Mismatches",
                 f"<div style='display: grid; grid-template-columns: 1fr 1fr; gap: 24px;'><div><h4>Whitespace Issues</h4>{ws_content}</div><div><h4>Numeric as String</h4>{num_str_content}</div></div>",
                 "Issues related to string formatting and data type storage."))

        # --- 5. Advanced Structural Insights ---
        # High Cardinality, Quasi-constant, Unique Candidates, Correlation
        
        card_content = ""
        if high_card:
            hc_rows = [[x['column'], f"{x['unique_count']:,}"] for x in high_card]
            card_content += f"<div style='margin-bottom: 24px'><h4>High Cardinality (Categorical)</h4>{_create_table(['Column', 'Unique Count'], hc_rows)}</div>"
        
        if quasi_constant:
            qc_rows = [[x['column'], f"{x['dominance_pct']}%"] for x in quasi_constant]
            card_content += f"<div style='margin-bottom: 24px'><h4>Quasi-Constant Columns (>99% same)</h4>{_create_table(['Column', 'Dominance %'], qc_rows)}</div>"
            
        if unique_candidates:
            card_content += f"<div style='margin-bottom: 24px'><h4>Unique ID Candidates (100% Unique)</h4><p>{', '.join(['<code>'+c+'</code>' for c in unique_candidates])}</p></div>"
            
        if high_corr:
            corr_rows = [[x['col1'], x['col2'], x['correlation']] for x in high_corr]
            card_content += f"<div><h4>High Correlation (> 0.95)</h4>{_create_table(['Column A', 'Column B', 'Corr'], corr_rows)}</div>"

        if card_content:
            all_details_html.append(_create_card("Structural Insights", card_content, "Deeper patterns in your table structure."))


        # --- Final Assembly ---
        if not all_details_html:
             all_details_html.append("<div class='details-card'><h3>✅ Good News!</h3><p>No significant data quality issues were found across the 12 checks.</p></div>")

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details for data quality complete.")
        return {
            "details_html": final_html,
            "visuals": [] 
        }

    except Exception as e:
        error_message = f"Failed during data quality visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}