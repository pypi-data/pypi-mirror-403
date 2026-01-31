"""Tests for mermaid_rs Python bindings.

This test suite captures the current behavior of mermaid-rs-renderer,
including known issues and panics. Tests are designed to detect when
upstream behavior changes.
"""

import pytest

# =============================================================================
# Basic Import and API Tests
# =============================================================================


def test_import():
    """Test that the module can be imported."""
    import mermaid_rs

    assert hasattr(mermaid_rs, "render")
    assert hasattr(mermaid_rs, "render_with_timing")
    assert hasattr(mermaid_rs, "supported_diagram_types")


def test_supported_diagram_types():
    """Test that supported_diagram_types returns expected types."""
    import mermaid_rs

    types = mermaid_rs.supported_diagram_types()

    assert isinstance(types, list)
    # Core diagram types that should always be present
    expected_types = [
        "flowchart",
        "graph",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram-v2",
        "erDiagram",
        "pie",
        "gantt",
        "gitGraph",
    ]
    for t in expected_types:
        assert t in types, f"Expected diagram type '{t}' not found"


# =============================================================================
# Theme and Options Tests
# =============================================================================


def test_render_with_theme_modern():
    """Test rendering with modern theme."""
    import mermaid_rs

    svg = mermaid_rs.render("flowchart LR; A-->B", theme="modern")
    assert "<svg" in svg


def test_render_with_theme_mermaid_default():
    """Test rendering with mermaid_default theme."""
    import mermaid_rs

    svg = mermaid_rs.render("flowchart LR; A-->B", theme="mermaid_default")
    assert "<svg" in svg


def test_render_invalid_theme():
    """Test that invalid theme raises ValueError."""
    import mermaid_rs

    with pytest.raises(ValueError, match="Unknown theme"):
        mermaid_rs.render("flowchart LR; A-->B", theme="invalid_theme")


def test_render_with_spacing():
    """Test rendering with custom spacing."""
    import mermaid_rs

    svg = mermaid_rs.render(
        "flowchart LR; A-->B-->C",
        node_spacing=100.0,
        rank_spacing=100.0,
    )
    assert "<svg" in svg


def test_render_with_timing():
    """Test render_with_timing returns timing info."""
    import mermaid_rs

    svg, parse_us, layout_us, render_us, total_us = mermaid_rs.render_with_timing(
        "flowchart LR; A-->B"
    )

    assert "<svg" in svg
    assert parse_us >= 0
    assert layout_us >= 0
    assert render_us >= 0
    assert total_us == parse_us + layout_us + render_us


# =============================================================================
# Flowchart Direction Tests
# =============================================================================


@pytest.mark.parametrize("direction", ["LR", "RL", "TD", "TB", "BT"])
def test_flowchart_directions(direction):
    """Test all flowchart directions work."""
    import mermaid_rs

    svg = mermaid_rs.render(f"flowchart {direction}; A-->B")
    assert "<svg" in svg


def test_graph_alias():
    """Test that 'graph' works as alias for 'flowchart'."""
    import mermaid_rs

    svg = mermaid_rs.render("graph LR; A-->B")
    assert "<svg" in svg


# =============================================================================
# Node Shape Tests
# =============================================================================


@pytest.mark.parametrize(
    "node_syntax,name",
    [
        ("A[Rectangle]", "rectangle"),
        ("A(Round)", "round"),
        ("A([Stadium])", "stadium"),
        ("A{Diamond}", "diamond"),
        ("A{{Hexagon}}", "hexagon"),
        ("A((Circle))", "circle"),
        ("A>Asymmetric]", "asymmetric"),
        ("A[/Parallelogram/]", "parallelogram"),
        ("A[/Trapezoid\\]", "trapezoid"),
    ],
)
def test_node_shapes(node_syntax, name):
    """Test various node shapes render correctly."""
    import mermaid_rs

    svg = mermaid_rs.render(f"flowchart LR; {node_syntax}-->B")
    assert "<svg" in svg, f"Node shape '{name}' failed to render"


# =============================================================================
# Edge Style Tests
# =============================================================================


@pytest.mark.parametrize(
    "edge_syntax,name",
    [
        ("A-->B", "arrow"),
        ("A---B", "open"),
        ("A-.->B", "dotted"),
        ("A==>B", "thick"),
        ("A~~~B", "invisible"),
    ],
)
def test_edge_styles(edge_syntax, name):
    """Test various edge styles render correctly."""
    import mermaid_rs

    svg = mermaid_rs.render(f"flowchart LR; {edge_syntax}")
    assert "<svg" in svg, f"Edge style '{name}' failed to render"


@pytest.mark.parametrize("dashes", [3, 4, 5])
def test_extended_arrows(dashes):
    """Test extended arrows (multiple dashes) work."""
    import mermaid_rs

    arrow = "-" * dashes + ">"
    svg = mermaid_rs.render(f"flowchart LR; A{arrow}B")
    assert "<svg" in svg


# =============================================================================
# Known Panic Cases - Edge Labels
# These tests document panics in dagre_rust that should be fixed upstream.
# When upstream fixes these, the tests will start passing (xfail will fail).
# =============================================================================


@pytest.mark.xfail(
    reason="Edge labels cause panic in dagre_rust (dagre_rust-0.0.5/src/layout/mod.rs:390:61)",
    raises=BaseException,  # PanicException inherits from BaseException, not Exception
    strict=True,  # Fail if this unexpectedly passes (meaning upstream fixed it)
)
@pytest.mark.parametrize(
    "diagram,name",
    [
        ("flowchart LR; A-->|text|B", "edge_label_lr"),
        ("flowchart TD; A-->|Yes|B", "edge_label_td"),
        ("flowchart LR; A-->|one|B-->|two|C", "edge_label_multi"),
    ],
)
def test_edge_labels_known_panic(diagram, name):
    """Edge labels cause panic in dagre_rust (known issue).

    Bug location: dagre_rust-0.0.5/src/layout/mod.rs:390:61
    When this test starts passing, the upstream bug has been fixed.
    """
    import mermaid_rs

    svg = mermaid_rs.render(diagram)
    assert "<svg" in svg


# =============================================================================
# Known Panic Cases - State Diagram Transitions
# =============================================================================


@pytest.mark.xfail(
    reason="State transition labels cause panic in dagre_rust",
    raises=BaseException,  # PanicException inherits from BaseException, not Exception
    strict=True,
)
def test_state_transition_with_label_known_panic():
    """State transition with label causes panic (known issue).

    This documents a bug in dagre_rust with labeled state transitions.
    """
    import mermaid_rs

    svg = mermaid_rs.render("stateDiagram-v2; A --> B: event")
    assert "<svg" in svg


def test_state_basic_works():
    """Basic state diagram (without labeled transitions) works."""
    import mermaid_rs

    # These should work
    assert "<svg" in mermaid_rs.render("stateDiagram-v2; [*] --> Active")
    assert "<svg" in mermaid_rs.render("stateDiagram-v2; Active --> [*]")


# =============================================================================
# Known Panic Cases - Unicode
# =============================================================================


@pytest.mark.xfail(
    reason="Parser incorrectly indexes multi-byte Unicode (parser.rs:5005:52)",
    raises=BaseException,  # PanicException inherits from BaseException, not Exception
    strict=True,
)
@pytest.mark.parametrize(
    "diagram,name",
    [
        ("flowchart LR; A[日本語]-->B[テスト]", "japanese"),
        ("flowchart LR; A[🎉]-->B[🚀]", "emoji"),
    ],
)
def test_unicode_known_panic(diagram, name):
    """Certain Unicode characters cause parser panic (known issue).

    Bug location: mermaid-rs-renderer/src/parser.rs:5005:52
    The parser incorrectly indexes into multi-byte Unicode characters.
    When this test starts passing, the upstream bug has been fixed.
    """
    import mermaid_rs

    svg = mermaid_rs.render(diagram)
    assert "<svg" in svg


def test_unicode_chinese_works():
    """Chinese characters work (different byte patterns than Japanese)."""
    import mermaid_rs

    # Chinese works while Japanese doesn't - likely due to specific byte patterns
    svg = mermaid_rs.render("flowchart LR; A[中文]-->B[测试]")
    assert "<svg" in svg


# =============================================================================
# Diagram Type Tests - Working Types
# =============================================================================


def test_render_simple_flowchart():
    """Test rendering a simple flowchart."""
    import mermaid_rs

    svg = mermaid_rs.render("flowchart LR; A-->B")
    assert "<svg" in svg
    assert "</svg>" in svg


def test_render_sequence_diagram():
    """Test rendering a sequence diagram."""
    import mermaid_rs

    svg = mermaid_rs.render("sequenceDiagram; Alice->>Bob: Hello")
    assert "<svg" in svg


def test_render_class_diagram():
    """Test rendering a class diagram."""
    import mermaid_rs

    svg = mermaid_rs.render("classDiagram; Animal <|-- Duck")
    assert "<svg" in svg


def test_render_er_diagram():
    """Test rendering an ER diagram."""
    import mermaid_rs

    svg = mermaid_rs.render("erDiagram; CUSTOMER ||--o{ ORDER : places")
    assert "<svg" in svg


def test_render_pie_chart():
    """Test rendering a pie chart."""
    import mermaid_rs

    svg = mermaid_rs.render('pie; "Dogs" : 10; "Cats" : 20')
    assert "<svg" in svg


def test_render_gantt():
    """Test rendering a gantt chart."""
    import mermaid_rs

    svg = mermaid_rs.render(
        "gantt; title Tasks; section S1; Task1 :a1, 2024-01-01, 30d"
    )
    assert "<svg" in svg


def test_render_gitgraph():
    """Test rendering a git graph."""
    import mermaid_rs

    svg = mermaid_rs.render("gitGraph; commit; branch dev; commit")
    assert "<svg" in svg


def test_render_timeline():
    """Test rendering a timeline."""
    import mermaid_rs

    svg = mermaid_rs.render("timeline; title History; 2000 : Event1")
    assert "<svg" in svg


def test_render_mindmap():
    """Test rendering a mindmap."""
    import mermaid_rs

    svg = mermaid_rs.render("mindmap; root((Central))")
    assert "<svg" in svg


def test_render_xychart():
    """Test rendering an XY chart."""
    import mermaid_rs

    svg = mermaid_rs.render("xychart-beta; x-axis [a,b,c]; bar [1,2,3]")
    assert "<svg" in svg


def test_render_quadrant():
    """Test rendering a quadrant chart."""
    import mermaid_rs

    svg = mermaid_rs.render("quadrantChart; title Chart; Campaign A: [0.3, 0.6]")
    assert "<svg" in svg


# =============================================================================
# Complex Flowchart Tests
# =============================================================================


def test_multiline_flowchart():
    """Test rendering a multiline flowchart."""
    import mermaid_rs

    diagram = """
    flowchart TD
        A[Start] --> B{Decision}
        B --> C[OK]
        B --> D[End]
    """
    svg = mermaid_rs.render(diagram)
    assert "<svg" in svg


def test_flowchart_with_subgraph():
    """Test flowchart with subgraphs."""
    import mermaid_rs

    svg = mermaid_rs.render("flowchart LR; subgraph S1; A-->B; end")
    assert "<svg" in svg


def test_flowchart_cycle():
    """Test flowchart with cycles."""
    import mermaid_rs

    svg = mermaid_rs.render("flowchart LR; A-->B-->C-->A")
    assert "<svg" in svg


def test_flowchart_many_nodes():
    """Test flowchart with many nodes."""
    import mermaid_rs

    # 20 sequential nodes
    nodes = "; ".join(f"N{i}-->N{i + 1}" for i in range(20))
    svg = mermaid_rs.render(f"flowchart LR; {nodes}")
    assert "<svg" in svg


# =============================================================================
# Edge Cases - Input Validation
# These document the library's lenient parsing behavior.
# =============================================================================


def test_empty_string_produces_svg():
    """Empty string produces empty SVG (lenient parsing)."""
    import mermaid_rs

    svg = mermaid_rs.render("")
    assert "<svg" in svg  # Library is lenient


def test_whitespace_only_produces_svg():
    """Whitespace-only input produces SVG (lenient parsing)."""
    import mermaid_rs

    svg = mermaid_rs.render("   \n\t  ")
    assert "<svg" in svg


def test_random_text_produces_svg():
    """Random text is treated as node labels (lenient parsing)."""
    import mermaid_rs

    # Library interprets this as node label, not as invalid
    svg = mermaid_rs.render("hello world")
    assert "<svg" in svg


def test_incomplete_arrow_produces_svg():
    """Incomplete arrow syntax still produces SVG."""
    import mermaid_rs

    svg = mermaid_rs.render("flowchart LR; A-->")
    assert "<svg" in svg


def test_special_chars_html():
    """HTML-like tags in labels are preserved (potential XSS if used unsafely)."""
    import mermaid_rs

    svg = mermaid_rs.render("flowchart LR; A[<b>Bold</b>]-->B")
    assert "<svg" in svg
    # Note: Tags are NOT escaped - be careful with user input!


def test_very_long_label():
    """Very long labels work but produce wide SVG."""
    import mermaid_rs

    long_label = "x" * 500
    svg = mermaid_rs.render(f"flowchart LR; A[{long_label}]-->B")
    assert "<svg" in svg


def test_comments_work():
    """Mermaid comments (%%) work."""
    import mermaid_rs

    svg = mermaid_rs.render("flowchart LR; A-->B; %% this is a comment")
    assert "<svg" in svg


# =============================================================================
# Regression Tests
# These should catch if upstream changes behavior unexpectedly.
# =============================================================================


def test_svg_has_expected_structure():
    """Verify SVG has expected attributes."""
    import mermaid_rs

    svg = mermaid_rs.render("flowchart LR; A-->B")

    assert 'xmlns="http://www.w3.org/2000/svg"' in svg
    assert "width=" in svg
    assert "height=" in svg
    assert "viewBox=" in svg
    assert "</svg>" in svg


def test_timing_is_reasonable():
    """Verify timing values are in reasonable range."""
    import mermaid_rs

    svg, parse_us, layout_us, render_us, total_us = mermaid_rs.render_with_timing(
        "flowchart LR; A-->B-->C-->D-->E"
    )

    # Should complete in under 100ms (100000 us) for simple diagram
    assert total_us < 100000, f"Rendering took too long: {total_us}us"
    # Should take at least some time (not 0)
    assert total_us > 0
