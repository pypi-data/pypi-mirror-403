def render(
    diagram: str,
    theme: str | None = None,
    node_spacing: float | None = None,
    rank_spacing: float | None = None,
) -> str:
    """Render a Mermaid diagram to SVG.

    Args:
        diagram: Mermaid diagram text
        theme: Optional theme name ("modern" or "mermaid_default")
        node_spacing: Optional custom node spacing
        rank_spacing: Optional custom rank spacing

    Returns:
        SVG string

    Raises:
        ValueError: If diagram syntax is invalid or theme is unknown

    Example:
        >>> import mermaid_rs
        >>> svg = mermaid_rs.render("flowchart LR; A-->B-->C")
        >>> assert "<svg" in svg
    """
    ...

def render_with_timing(
    diagram: str,
) -> tuple[str, int, int, int, int]:
    """Render a Mermaid diagram to SVG with timing information.

    Args:
        diagram: Mermaid diagram text

    Returns:
        Tuple of (svg_string, parse_microseconds, layout_microseconds,
                  render_microseconds, total_microseconds)

    Raises:
        ValueError: If diagram syntax is invalid
    """
    ...

def supported_diagram_types() -> list[str]:
    """Get list of supported diagram types.

    Returns:
        List of supported diagram type names including:
        - flowchart / graph
        - sequenceDiagram
        - classDiagram
        - stateDiagram-v2
        - erDiagram
        - pie
        - xychart
        - quadrantChart
        - gantt
        - timeline
        - journey
        - mindmap
        - gitGraph
    """
    ...

class RenderResult:
    """Result of rendering with detailed timing information."""

    svg: str
    """The rendered SVG string."""

    parse_us: int
    """Time spent parsing (microseconds)."""

    layout_us: int
    """Time spent computing layout (microseconds)."""

    render_us: int
    """Time spent rendering to SVG (microseconds)."""

    @property
    def total_us(self) -> int:
        """Total render time in microseconds."""
        ...

    @property
    def total_ms(self) -> float:
        """Total render time in milliseconds."""
        ...
