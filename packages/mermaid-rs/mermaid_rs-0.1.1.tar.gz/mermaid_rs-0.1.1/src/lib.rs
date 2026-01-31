use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Render a Mermaid diagram to SVG.
///
/// Args:
///     diagram: Mermaid diagram text
///     theme: Optional theme name ("modern" or "mermaid_default")
///     node_spacing: Optional custom node spacing
///     rank_spacing: Optional custom rank spacing
///
/// Returns:
///     SVG string
///
/// Example:
///     >>> import mermaid_rs
///     >>> svg = mermaid_rs.render("flowchart LR; A-->B-->C")
///     >>> print(svg[:50])
///     <svg xmlns="http://www.w3.org/2000/svg"...
#[pyfunction]
#[pyo3(signature = (diagram, theme=None, node_spacing=None, rank_spacing=None))]
fn render(
    diagram: &str,
    theme: Option<&str>,
    node_spacing: Option<f32>,
    rank_spacing: Option<f32>,
) -> PyResult<String> {
    let mut options = mermaid_rs_renderer::RenderOptions::default();

    // Apply theme if specified
    if let Some(theme_name) = theme {
        options.theme = match theme_name {
            "modern" => mermaid_rs_renderer::Theme::modern(),
            "mermaid_default" => mermaid_rs_renderer::Theme::mermaid_default(),
            _ => {
                return Err(PyValueError::new_err(format!(
                    "Unknown theme: '{}'. Available: 'modern', 'mermaid_default'",
                    theme_name
                )));
            }
        };
    }

    // Apply spacing options
    if let Some(spacing) = node_spacing {
        options.layout.node_spacing = spacing;
    }
    if let Some(spacing) = rank_spacing {
        options.layout.rank_spacing = spacing;
    }

    mermaid_rs_renderer::render_with_options(diagram, options)
        .map_err(|e| PyValueError::new_err(format!("Render error: {}", e)))
}

/// Render a Mermaid diagram to SVG with timing information.
///
/// Returns a tuple of (svg, parse_us, layout_us, render_us, total_us).
///
/// Args:
///     diagram: Mermaid diagram text
///
/// Returns:
///     Tuple of (svg_string, parse_microseconds, layout_microseconds, render_microseconds, total_microseconds)
#[pyfunction]
fn render_with_timing(diagram: &str) -> PyResult<(String, u128, u128, u128, u128)> {
    let result = mermaid_rs_renderer::render_with_timing(
        diagram,
        mermaid_rs_renderer::RenderOptions::default(),
    )
    .map_err(|e| PyValueError::new_err(format!("Render error: {}", e)))?;

    let total = result.total_us();
    Ok((
        result.svg,
        result.parse_us,
        result.layout_us,
        result.render_us,
        total,
    ))
}

/// Get list of supported diagram types.
///
/// Returns:
///     List of supported diagram type names
#[pyfunction]
fn supported_diagram_types() -> Vec<&'static str> {
    vec![
        "flowchart",
        "graph",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram-v2",
        "erDiagram",
        "pie",
        "xychart",
        "quadrantChart",
        "gantt",
        "timeline",
        "journey",
        "mindmap",
        "gitGraph",
    ]
}

/// RenderResult class for detailed timing information
#[pyclass]
struct RenderResult {
    #[pyo3(get)]
    svg: String,
    #[pyo3(get)]
    parse_us: u128,
    #[pyo3(get)]
    layout_us: u128,
    #[pyo3(get)]
    render_us: u128,
}

#[pymethods]
impl RenderResult {
    /// Total render time in microseconds
    #[getter]
    fn total_us(&self) -> u128 {
        self.parse_us + self.layout_us + self.render_us
    }

    /// Total render time in milliseconds
    #[getter]
    fn total_ms(&self) -> f64 {
        self.total_us() as f64 / 1000.0
    }

    fn __repr__(&self) -> String {
        format!(
            "RenderResult(total={:.2}ms, parse={}us, layout={}us, render={}us)",
            self.total_ms(),
            self.parse_us,
            self.layout_us,
            self.render_us
        )
    }
}

#[pymodule(gil_used = false)]
fn mermaid_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(render, m)?)?;
    m.add_function(wrap_pyfunction!(render_with_timing, m)?)?;
    m.add_function(wrap_pyfunction!(supported_diagram_types, m)?)?;
    m.add_class::<RenderResult>()?;
    Ok(())
}
