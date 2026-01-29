# ==============================================================================
# FILE: 3_Source_Code/decyphr/__init__.py
# ==============================================================================
# PURPOSE: This file serves as the main entry point to the decyphr library.
#          It defines the public API and handles Jupyter Notebook integration.

# --- Import necessary libraries ---
import os
from typing import Optional

# --- Define the project version ---
__version__ = "1.1.1"

# --- Import core components ---
from .main_orchestrator import run_analysis_pipeline


def _is_notebook() -> bool:
    """
    Checks if the code is being run in a Jupyter-like environment.
    """
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        else:
            return False
    except NameError:
        return False      # Standard Python interpreter

def analyze(
    filepath: str,
    target: Optional[str] = None,
    compare_filepath: Optional[str] = None
):
    """
    Generates a deep, interactive EDA report for a given dataset.

    When run in a Jupyter Notebook, it will display the report inline.
    Otherwise, it will print the path to the saved HTML file.

    Args:
        filepath (str): The path to the primary data file (CSV or Excel).
        target (str, optional): The name of the target column for predictive analysis.
        compare_filepath (str, optional): Path to a second dataframe for comparison.
    """
    # This function generates the report and returns its path
    report_path_relative = run_analysis_pipeline(
        filepath=filepath,
        target=target,
        compare_filepath=compare_filepath
    )

    if report_path_relative:
        report_path_absolute = os.path.abspath(report_path_relative)

        if _is_notebook():
            try:
                from IPython.display import display, HTML

                # --- CORRECTED LOGIC FOR JUPYTER ---
                # 1. Read the entire content of the generated HTML file.
                with open(report_path_absolute, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # 2. Use IPython.display.HTML to render the raw HTML string.
                # This bypasses all IFrame security issues.
                print("Displaying report in notebook...")
                display(HTML(f"<p>Report also saved at: {report_path_absolute}</p>"))
                display(HTML(html_content))
                
            except Exception as e:
                print(f"Decyphr ⚠️: Could not display report directly in notebook. Error: {e}")
                print(f"Report is available at: {report_path_absolute}")

        else:
            # For standard Python scripts, just print the path.
            print(f"\nDecyphr 📄: Report successfully saved to '{report_path_absolute}'")
    
    return None # The function's main purpose is to display or print, not return a value.

# --- Define what is publicly available ---
__all__ = [
    'analyze',
    '__version__'
]

print(f"Decyphr 🔮 v{__version__}: Ready to analyze.")
