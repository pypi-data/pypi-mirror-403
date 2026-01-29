/* ==========================================================================
   FILE: 3_Source_Code/decyphr/report_builder/assets/scripts/interactivity.js
   PURPOSE: Handles all client-side interactivity for the Decyphr report,
            including theme switching, lazy plot rendering, and tabbed navigation.
   VERSION: 4.0 (Professional Redesign with Lazy Loading)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

    // --- Global State & Element Selection ---
    const body = document.body;
    const themeToggleButton = document.getElementById('theme-toggle');
    const navLinks = document.querySelectorAll('.top-nav a.nav-link');
    const contentPanels = document.querySelectorAll('.content-panel');

    // --- 1. Load and Parse Embedded Plot Data ---
    const plotDataElement = document.getElementById('plot-data');
    const ALL_PLOTS_DATA = JSON.parse(plotDataElement.textContent || '{}');
    let renderedSections = new Set(); // Keep track of which sections have been rendered

    // --- 2. Theme Management Module ---
    const applyTheme = (theme) => {
        body.setAttribute('data-theme', theme);
        localStorage.setItem('decyphrTheme', theme);
        // We only update themes for plots that are already visible
        updateVisiblePlotlyThemes(theme);
    };

    const layoutUpdate = {
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#f4f4f4',
        font: { color: '#000000' },
        xaxis: { gridcolor: '#cccccc' },
        yaxis: { gridcolor: '#cccccc' }
    };

    const updateVisiblePlotlyThemes = (theme) => {
        const layoutUpdate = theme === 'dark'
            ? { paper_bgcolor: '#1e293b', plot_bgcolor: 'rgba(0,0,0,0)', font: { color: '#e2e8f0' }, 'xaxis.gridcolor': '#334155', 'yaxis.gridcolor': '#334155', 'legend.bgcolor': 'rgba(0,0,0,0.3)' }
            : { paper_bgcolor: '#ffffff', plot_bgcolor: 'rgba(0,0,0,0)', font: { color: '#0f172a' }, 'xaxis.gridcolor': '#e5e7eb', 'yaxis.gridcolor': 'rgba(255,255,255,0.7)' };

        document.querySelectorAll('.plot-placeholder:not(:empty) .js-plotly-plot').forEach(plotDiv => {
            if (plotDiv.data) {
                Plotly.relayout(plotDiv, layoutUpdate);
            }
        });
    };

    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            const newTheme = body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    // --- 3. Lazy Plot Rendering Module ---
    const renderPlotsForSection = (sectionId) => {
        // Only render a section's plots once to save resources
        if (renderedSections.has(sectionId)) {
            return;
        }

        const plotDataForSection = ALL_PLOTS_DATA[sectionId];
        if (!plotDataForSection || plotDataForSection.length === 0) {
            renderedSections.add(sectionId); // Mark as "rendered" even if no plots
            return;
        }

        console.log(`Lazy loading plots for section: ${sectionId}`);

        plotDataForSection.forEach((plotJson, index) => {
            const placeholderId = `plot-${sectionId}-${index}`;
            const placeholderDiv = document.getElementById(placeholderId);
            if (placeholderDiv) {
                // Use Plotly.newPlot to draw the chart from its JSON definition
                Plotly.newPlot(placeholderDiv, plotJson.data, plotJson.layout, { responsive: true, displayModeBar: false });
            }
        });

        renderedSections.add(sectionId);
        // Apply the current theme to the newly rendered plots
        updateVisiblePlotlyThemes(body.getAttribute('data-theme'));
    };

    // --- 4. Tabbed Navigation Module ---
    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const targetSectionId = link.getAttribute('data-section-id');

            // Update Navigation Link states
            navLinks.forEach(nav => nav.classList.remove('active'));
            link.classList.add('active');

            // Update Content Panel visibility
            contentPanels.forEach(panel => {
                const isActive = panel.id === `panel-${targetSectionId}`;
                panel.classList.toggle('active', isActive);
                // Explicitly handle inline styles set by the template
                panel.style.display = isActive ? 'block' : 'none';
            });

            // CRITICAL: Render plots for the newly visible section
            renderPlotsForSection(targetSectionId);

            // Scroll to top of content area on tab switch
            document.querySelector('.main-content').scrollTop = 0;
        });
    });

    // --- 5. Initial Page Load Logic ---
    const savedTheme = localStorage.getItem('decyphrTheme') || 'dark';
    applyTheme(savedTheme);

    // Render plots for the initially active section on page load
    const initialActiveSection = document.querySelector('.content-panel.active');
    if (initialActiveSection) {
        const initialSectionId = initialActiveSection.id.replace('panel-', '');
        renderPlotsForSection(initialSectionId);
    }
});