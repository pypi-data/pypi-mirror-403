# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p14_deep_text_analysis/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Deep Text Analysis (NLP), 
#          visualizing 15+ metrics/features using Antigravity UI.

import plotly.graph_objects as go
import pandas as pd
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

def _create_table(headers: List[str], rows: List[List[Any]], overflow: bool = False, centered_cols: List[int] = []) -> str:
    """Creates a standard transparent Antigravity table."""
    if not rows: return "<p style='color: var(--text-tertiary); font-style: italic;'>No relevant data.</p>"
    
    thead = "".join([f"<th>{h}</th>" for h in headers])
    tbody = ""
    for row in rows:
        row_html = ""
        for i, cell in enumerate(row):
             style = "text-align: center;" if i in centered_cols else ""
             row_html += f"<td style='{style}'>{cell}</td>"
        tbody += f"<tr>{row_html}</tr>"
    
    wrapper_class = "table-responsive" if overflow else ""
    return f"""
    <div class='{wrapper_class}'>
        <table class='details-table'>
            <thead><tr>{thead}</tr></thead>
            <tbody>{tbody}</tbody>
        </table>
    </div>
    """

def _create_pill(text: str, color: str = "var(--primary-accent)") -> str:
     return f"<span style='background: {color}33; color: {color}; padding: 4px 12px; border-radius: 12px; font-size: 0.9em; margin-right: 8px;'>{text}</span>"

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content for NLP analysis.
    """
    print("     -> Generating details & visualizations for Advanced Text Analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Deep text analysis was not performed."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        for col_name, res in analysis_results.items():
            print(f"        - Creating visuals for text column '{col_name}'")
            
            # --- 1. Metrics & Readability Card ---
            sentiment = res.get('sentiment', {})
            read_score = res.get('readability_score', 0)
            len_stats = res.get('length_stats', {})
            pii_risk = res.get('pii_risk', {})
            lang = res.get('lang_detect', 'Unknown')
            
            # Gauge for Sentiment
            fig_pol = go.Figure(go.Indicator(
                mode="gauge+number", value=sentiment.get('mean_polarity', 0),
                title={'text': f"Sentiment (Polarity) - {col_name}<br><span style='font-size:0.8em;color:gray'>-1 (Neg) to +1 (Pos)</span>"},
                gauge={'axis': {'range': [-1, 1]}, 'bar': {'color': THEME_COLORS["primary_accent"]}}
            ))
            fig_pol = apply_antigravity_theme(fig_pol)
            fig_pol.update_layout(height=300)
            all_visuals.append(fig_pol)
            
            # Stat Table
            rows = [
                ["Detected Language", lang],
                ["Avg Readability (Flesch)", f"{read_score:.1f} (0-100)"],
                ["Avg Word Count", f"{len_stats.get('avg_words', 0):.1f}"],
                ["Subjectivity", f"{sentiment.get('mean_subjectivity', 0):.2f}"]
            ]
            
            # PII Alert
            pii_html = ""
            if pii_risk.get('emails_detected', 0) > 0 or pii_risk.get('phones_detected', 0) > 0:
                pii_html = f"<br><p style='color: var(--danger);'>⚠️ PII Detected: {pii_risk}</p>"

            all_details_html.append(_create_card(f"Text Health: {col_name}", 
                 _create_table(["Metric", "Value"], rows) + pii_html,
                 "Structural and quality metrics for the text corpus."))

            # --- 2. Keywords & Entities ---
            keywords = res.get('keywords_tfidf', [])
            bigrams = res.get('top_bigrams', [])
            entities = res.get('top_entities', {})
            
            kw_html = ""
            if keywords: kw_html += "<div><strong>Top Keywords:</strong><br>" + "".join([_create_pill(k) for k in keywords]) + "</div><br>"
            if bigrams:  kw_html += "<div><strong>Top Bigrams:</strong><br>" + "".join([_create_pill(b, "var(--secondary-accent)") for b in bigrams]) + "</div><br>"
            
            if entities:
                ent_rows = [[k, v] for k,v in entities.items()]
                kw_html += "<strong>Top Entities:</strong>" + _create_table(["Entity", "Count"], ent_rows)

            all_details_html.append(_create_card(f"Content Insights: {col_name}", kw_html, "What is the text actually about?"))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details and visualizations for Deep Text Analysis complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during text visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}