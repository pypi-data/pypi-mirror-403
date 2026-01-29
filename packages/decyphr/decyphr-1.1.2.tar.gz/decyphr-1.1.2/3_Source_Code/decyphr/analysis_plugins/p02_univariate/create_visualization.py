# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p02_univariate/create_visualization.py
# ==============================================================================
# PURPOSE: This file generates all visual components AND detailed HTML tables
#          for the univariate analysis section.

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from decyphr.utils.plotting import apply_antigravity_theme, get_theme_colors

# Get standard colors
THEME_COLORS = get_theme_colors()

def _create_kpi_metrics(stats: Dict[str, float]) -> str:
    """Generates a row of Big Number KPIs for the top of the card."""
    def _kpi_item(label, value, subtext=""):
        return f"""
        <div style='display: flex; flex-direction: column;'>
            <span class='kpi-label'>{label}</span>
            <span class='kpi-value'>{value}</span>
            {f"<span style='font-size: 0.85em; color: var(--text-tertiary);'>{subtext}</span>" if subtext else ""}
        </div>
        """
    
    kpis = []
    # 1. Total Count
    kpis.append(_kpi_item("Total", f"{stats.get('count', 0):,.0f}"))
    
    # 2. Missing
    missing_pct = stats.get('missing_pct', 0)
    kpis.append(_kpi_item("Missing", f"{missing_pct:.1f}%", f"{stats.get('missing', 0):,} rows"))
    
    # 3. Unique
    unique = stats.get('unique') or stats.get('total_unique')
    if unique:
        kpis.append(_kpi_item("Unique", f"{unique:,.0f}"))
        
    # 4. Mean (Numeric Only)
    if 'mean' in stats:
        kpis.append(_kpi_item("Mean", f"{stats['mean']:,.2f}"))
        
    kpi_html = "".join(kpis)
    return f"<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 32px; padding-bottom: 32px; margin-bottom: 32px; border-bottom: 1px solid var(--border-light);'>{kpi_html}</div>"


def _create_numeric_details_html(col_name: str, stats: Dict[str, float]) -> str:
    """Generates a minimalist table for remaining stats."""
    rows = []
    rows.append(("Std. Dev", f"{stats.get('std', 0):,.2f}"))
    rows.append(("Min", f"{stats.get('min', 0):,.2f}"))
    rows.append(("Median", f"{stats.get('50%', 0):,.2f}"))
    rows.append(("Max", f"{stats.get('max', 0):,.2f}"))
    rows.append(("Zeros", f"{stats.get('zeros', 0):,.0f}"))
    rows.append(("Outliers", f"{stats.get('outliers', 0):,.0f}"))
    
    table_html = "<table class='details-table'>"
    for label, val in rows:
        table_html += f"<tr><td>{label}</td><td style='text-align: right;'><strong>{val}</strong></td></tr>"
    table_html += "</table>"
    return table_html

def _create_categorical_details_html(col_name: str, stats: Dict[str, Any]) -> str:
    """Generates stats table for categorical columns."""
    rows = []
    rows.append(("Top Category", str(stats.get('top', 'N/A'))))
    rows.append(("Frequency", f"{stats.get('freq', 0):,}"))
    
    table_html = "<table class='details-table'>"
    for label, val in rows:
        table_html += f"<tr><td>{label}</td><td style='text-align: right;'><strong>{val}</strong></td></tr>"
    table_html += "</table>"
    return table_html

def _generate_numeric_insights(col_name: str, stats: Dict[str, float]) -> str:
    """Generates text insights."""
    insights = []
    
    # Skewness
    skew = stats.get('skew', 0)
    if abs(skew) > 1:
        direction = "positive (right)" if skew > 0 else "negative (left)"
        meaning = "frequent lower values with some high outliers" if skew > 0 else "frequent higher values with some low outliers"
        insights.append(f"Distribution is strongly skewed <strong>{direction}</strong>, indicating {meaning}.")
    
    # Missing Data
    if stats.get('missing_pct', 0) > 5:
        insights.append(f"Missing <span style='color: var(--status-warning-text); font-weight: bold;'>{stats.get('missing_pct'):.1f}%</span> of data.")
    
    # Outliers
    if stats.get('outliers', 0) > 0:
        outlier_pct = stats.get('outlier_pct', 0)
        insights.append(f"Detected <strong>{stats.get('outliers', 0):,.0f}</strong> outliers ({outlier_pct:.1f}%).")
        
    if not insights: return ""
    return "<ul style='color: var(--text-secondary); padding-left: 20px; line-height: 1.6;'>" + "".join([f"<li>{x}</li>" for x in insights]) + "</ul>"

def create_visuals(ddf, analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates Plotly visualizations and detailed HTML tables for univariate analysis.
    """
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}

    numeric_stats = analysis_results.get("numeric_stats", {})
    categorical_stats = analysis_results.get("categorical_stats", {})

    all_visuals: List[go.Figure] = []
    final_html_sections = []

    try:
        from plotly.subplots import make_subplots

        from plotly.subplots import make_subplots

        html_sections_list = []
        
        # --- 0. Navigation Chips (Jump to Column) ---
        # Collect all column names
        all_cols = list(numeric_stats.keys()) + list(categorical_stats.keys())
        all_cols.sort()
        
        nav_chips = []
        for col in all_cols:
             nav_chips.append(f"<a href='#col-{col}' class='nav-chip'>{col}</a>")
        
        nav_section = f"""
        <div class="chip-container-wrapper">
            <div class="chip-container">
                {''.join(nav_chips)}
            </div>
        </div>
        """
        html_sections_list.append(nav_section)

        # --- 1. Process Numeric Columns ---
        for col_name, stats in numeric_stats.items():
            
            kpi_section = _create_kpi_metrics(stats)
            
            # --- Rich Insights Generation ---
            insights = []
            
            # Skewness Interpretation
            skew = stats.get('skew', 0)
            if abs(skew) > 1:
                direction = "right (positive)" if skew > 0 else "left (negative)"
                meaning = "frequent lower values with typical high outliers" if skew > 0 else "frequent higher values with typical low outliers"
                insights.append(f"Distribution is strongly skewed <strong>{direction}</strong>, indicating {meaning}.")
            elif abs(skew) > 0.5:
                direction = "moderately right" if skew > 0 else "moderately left"
                insights.append(f"Distribution is {direction} skewed.")
            else:
                insights.append("Distribution is approximately symmetric.")
                
            # CV / Variability
            cv = stats.get('cv', 0)
            if cv > 1:
                insights.append(f"High variability detected (CV: {cv:.2f}), suggesting diverse data points relative to the mean.")
            elif cv < 0.1 and cv > 0:
                insights.append("Low variability; data points are clustered closely around the mean.")
                
            # Outliers
            outliers = stats.get('outliers', 0)
            if outliers > 0:
                outlier_pct = stats.get('outlier_pct', 0)
                sev = "High" if outlier_pct > 5 else "Moderate" if outlier_pct > 1 else "Low"
                insights.append(f"{sev} outlier presence: <strong>{outliers:,.0f}</strong> detected ({outlier_pct:.1f}%).")
            
            # Missing
            missing_pct = stats.get('missing_pct', 0)
            if missing_pct > 0:
                 insights.append(f"Variable has <strong>{missing_pct:.1f}%</strong> missing values.")

            insights_html = "<ul class='insight-list'>" + "".join([f"<li>{x}</li>" for x in insights]) + "</ul>"
            details_html = _create_numeric_details_html(col_name, stats)
            
            data_series = ddf[col_name].compute() 
            
            # --- Combined Marginal Plot (Box + Hist -> Line) ---
            # Using subplots to have a box plot on top of the frequency polygon
            fig = make_subplots(
                rows=2, cols=1,
                row_heights=[0.15, 0.85],
                shared_xaxes=True,
                vertical_spacing=0.03
            )
            
            # Top: Box Plot
            fig.add_trace(go.Box(
                x=data_series,
                name="",
                marker=dict(color='#505050'), # Dark grey to match bold theme
                line=dict(color='black', width=2),
                showlegend=False,
                boxmean=True # Show mean as dotted line
            ), row=1, col=1)
            
            # Bottom: Frequency Polygon (Line Chart instead of Histogram)
            # Calculate histogram bins manually
            counts, bin_edges = np.histogram(data_series, bins='auto')
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            fig.add_trace(go.Scatter(
                x=bin_centers,
                y=counts,
                name="Distribution",
                mode='lines+markers',
                line=dict(color='black', width=4), # Bold black line
                marker=dict(color='grey', size=8, symbol='circle', line=dict(color='black', width=1)), # Bold grey points
                fill='tozeroy', # Optional: minimal fill to ground it
                fillcolor='rgba(0,0,0,0.05)', # Very subtle fill
                showlegend=False
            ), row=2, col=1)
            
            fig = apply_antigravity_theme(fig, height=400)
            fig.update_layout(
                margin=dict(t=20, b=20, l=0, r=0),
                xaxis2_title=col_name,
                bargap=0.05
            )
            # Remove y-axis labels for box plot to save space, but keep x-axis shared
            fig.update_yaxes(showticklabels=False, row=1, col=1)
            fig.update_xaxes(showticklabels=False, row=1, col=1)

            all_visuals.append(fig)
            current_plot_index = len(all_visuals) - 1 # 0-based index
            
            # Note the ID attribute on the card for navigation
            # AND explicitly place the plot placeholder with the correct ID
            html_sections_list.append(f"""
            <div class='details-card' id='col-{col_name}'>
                <h3>{col_name} <span style='font-weight:300; font-size: 0.8em; color: var(--text-tertiary);'>Numeric</span></h3>
                {kpi_section}
                <div style='display: grid; grid-template-columns: 350px 1fr; gap: 48px;'>
                    <div>
                        <h4 style='font-size: 0.9rem; text-transform:uppercase; color:var(--text-secondary); margin-bottom:16px;'>Automated Insights</h4>
                        {insights_html}
                        <div style="margin-top: 32px;">
                            {details_html}
                        </div>
                    </div>
                    <div>
                         <div class="plot-placeholder" id="plot-p02_univariate-{current_plot_index}" style="width:100%; height:400px;"></div>
                    </div>
                </div>
            </div>
            """)

        # --- 2. Process Categorical Columns ---
        for col_name, stats in categorical_stats.items():
            
            kpi_section = _create_kpi_metrics(stats)
            details_html = _create_categorical_details_html(col_name, stats)
            
            # Insights
            insights = []
            if stats.get('is_high_cardinality'):
                insights.append("<strong>High Cardinality:</strong> Large number of unique values relative to rows. Possibly an ID or reference column.")
            
            top_cat = stats.get('mode', 'N/A')
            top_pct = stats.get('mode_pct', 0)
            unique = stats.get('total_unique', 0)

            insights.append(f"Most frequent category is '<strong>{top_cat}</strong>' ({top_pct:.1f}%).")
            
            if unique == 1:
                 insights.append("Constant column (only 1 unique value).")
            elif unique == 2:
                 insights.append("Binary column.")

            insights_html = "<ul class='insight-list'>" + "".join([f"<li>{x}</li>" for x in insights]) + "</ul>"

            
            # Extract cumulative data
            value_counts_data = stats.get("value_counts", {})
            labels = list(value_counts_data.keys())
            counts = [d['count'] for d in value_counts_data.values()]
            cum_pcts = [d['cumulative_pct'] for d in value_counts_data.values()]
            
            # --- Pareto Chart ---
            fig = go.Figure()
            
            # Bar (Counts)
            fig.add_trace(go.Bar(
                x=labels, y=counts,
                name="Count",
                marker=dict(color=THEME_COLORS["primary_accent"]),
                yaxis='y',
                opacity=0.8
            ))
            
            # Line (Cumulative %)
            fig.add_trace(go.Scatter(
                x=labels, y=cum_pcts,
                name="Cumulative %",
                mode='lines+markers',
                marker=dict(color=THEME_COLORS["warning"]),
                line=dict(width=2, dash='dot'),
                yaxis='y2'
            ))
            
            fig = apply_antigravity_theme(fig, height=400)
            fig.update_layout(
                yaxis=dict(title="Count"),
                yaxis2=dict(
                    title="Cumulative %",
                    overlaying='y',
                    side='right',
                    range=[0, 110], 
                    showgrid=False,
                    showticklabels=True
                ),
                legend=dict(x=0.0, y=1.1, orientation='h'),
                margin=dict(r=20, t=30) 
            )
            all_visuals.append(fig)
            current_plot_index = len(all_visuals) - 1

            html_sections_list.append(f"""
            <div class='details-card' id='col-{col_name}'>
                <h3>{col_name} <span style='font-weight:300; font-size: 0.8em; color: var(--text-tertiary);'>Categorical</span></h3>
                {kpi_section}
                <div style='display: grid; grid-template-columns: 350px 1fr; gap: 48px;'>
                    <div>
                         <h4 style='font-size: 0.9rem; text-transform:uppercase; color:var(--text-secondary); margin-bottom:16px;'>Automated Insights</h4>
                         {insights_html}
                         <div style="margin-top: 32px;">
                            {details_html}
                         </div>
                    </div>
                    <div>
                         <div class="plot-placeholder" id="plot-p02_univariate-{current_plot_index}" style="width:100%; height:400px;"></div>
                    </div>
                </div>
            </div>
            """)

        final_html = f"<div>{''.join(html_sections_list)}</div>"
        
        return {
            "details_html": final_html,
            "visuals": all_visuals,
            "suppress_plot_grid": True # Tell builder to NOT generate the default grid
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}