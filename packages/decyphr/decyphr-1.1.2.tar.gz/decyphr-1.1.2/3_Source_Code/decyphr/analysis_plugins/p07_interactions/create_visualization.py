# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p07_interactions/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Feature Interaction Analysis, 
#          visualizing 15+ feature engineering suggestions using Antigravity UI.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List
from decyphr.utils.plotting import apply_antigravity_theme, get_theme_colors

# Get standard colors
THEME_COLORS = get_theme_colors()

# --- Antigravity Helper Functions ---

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

def _create_list_card(title: str, items: List[str], subtitle: str = "") -> str:
    """Creates a card with a styled list."""
    if not items: return ""
    list_html = "<ul class='details-list'>" + "".join([f"<li><code>{item}</code></li>" for item in items]) + "</ul>"
    return _create_card(title, list_html, subtitle)

def _create_table(headers: List[str], rows: List[List[Any]], overflow: bool = False) -> str:
    """Creates a standard transparent Antigravity table."""
    if not rows: return "<p style='color: var(--text-tertiary); font-style: italic;'>No relevant data.</p>"
    
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
    Creates rich HTML content to display advanced feature interactions.
    """
    print("     -> Generating details for advanced feature interactions...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    
    all_details_html: List[str] = []

    try:
        # Extract Results
        numeric_ints = analysis_results.get("numeric_interactions", [])
        categorical_ints = analysis_results.get("categorical_interactions", [])
        ratio_suggs = analysis_results.get("ratio_suggestions", [])
        mixed_suggs = analysis_results.get("mixed_type_suggestions", [])
        top_scored = analysis_results.get("top_scored_interactions", [])
        target_used = analysis_results.get("target_used", "None")

        # --- 1. Top Scored Interactions (if available) ---
        if top_scored:
            rows = []
            for item in top_scored:
                rows.append([f"<code>{item['interaction']}</code>", f"<strong>{item['score']:.4f}</strong>"])
            
            all_details_html.append(_create_card(f"Top Interactions (Target: {target_used})", 
                _create_table(["Interaction Feature", "Correlation w/ Target"], rows),
                "Features created by combining variables that show the highest correlation with the prediction target."))

        # --- 2. Numeric Polynomials ---
        if numeric_ints:
            all_details_html.append(_create_list_card("Polynomial Interactions (Numeric)", 
                numeric_ints[:10], # Limit display
                "Multiplicative combinations of highly variant numeric features (Degree 2)."))

        # --- 3. Ratio Features ---
        if ratio_suggs:
            all_details_html.append(_create_list_card("Ratio Feature Candidates", 
                ratio_suggs[:10],
                "Division of features (A/B), useful for normalization (e.g., Price per Unit)."))

        # --- 4. Categorical Combinations ---
        if categorical_ints:
            all_details_html.append(_create_list_card("Categorical Cross-Products", 
                categorical_ints[:10],
                "Combinations of categorical variables (A & B) to capture specific sub-group behaviors."))

        # --- 5. Mixed Type Aggregations ---
        if mixed_suggs:
            all_details_html.append(_create_list_card("Grouped Statistics Suggestions", 
                mixed_suggs[:5],
                "Aggregation features: computing statistics of a number grouped by a category."))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details for feature interactions complete.")
        return {
            "details_html": final_html,
            "visuals": [] 
        }

    except Exception as e:
        error_message = f"Failed during feature interaction visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}