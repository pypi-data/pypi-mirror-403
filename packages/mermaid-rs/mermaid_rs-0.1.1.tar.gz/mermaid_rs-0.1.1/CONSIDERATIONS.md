# Python Bindings for mermaid-rs-renderer: Considerations

## Project Overview

This document outlines the key considerations for creating Python bindings for [mermaid-rs-renderer](https://github.com/1jehuang/mermaid-rs-renderer), using [python-ripgrep](https://github.com/phil65/python-ripgrep) (ripgrep_rs) as a reference.

## Key Differences from ripgrep_rs

### 1. Dependency Sourcing

**ripgrep_rs approach**: Uses crates.io dependencies directly (grep, ignore, etc.)

**mermaid-rs-renderer challenges**:
- **Not published to crates.io** (as of analysis date)
- Uses a **patched local dependency** (`dagre_rust`) via `[patch.crates-io]`
- The vendored `dagre_rust` is at `vendor/dagre_rust`

**Options for dependency management**:

```toml
# Option 1: Git dependency (current Cargo.toml)
mermaid-rs-renderer = { git = "https://github.com/1jehuang/mermaid-rs-renderer", default-features = false }

# Option 2: Vendor the entire mermaid-rs-renderer (most reliable)
# - Clone repo into vendor/mermaid-rs-renderer
# - Include their vendor/dagre_rust
mermaid-rs-renderer = { path = "vendor/mermaid-rs-renderer", default-features = false }

# Option 3: Wait for crates.io publication
mermaid-rs-renderer = { version = "0.1", default-features = false }
```

**Recommendation**: Start with Git dependency for development, then either:
- Request the author to publish to crates.io
- Or vendor the dependency for reproducible builds

### 2. Rust Edition

**mermaid-rs-renderer uses**: `edition = "2024"` (Rust 2024)
**ripgrep_rs uses**: `edition = "2024"` (Rust 2024)

Both use Rust 2024, which requires Rust 1.85+. This is current and matches the reference project.

### 3. Feature Flags

mermaid-rs-renderer has feature flags to consider:

```toml
[features]
default = ["cli", "png"]
cli = ["dep:clap"]      # CLI support - NOT needed for Python bindings
png = ["dep:resvg", "dep:usvg"]  # PNG support - optional
```

**Recommendation**: Disable default features to minimize dependencies:
```toml
mermaid-rs-renderer = { ..., default-features = false }
```

This removes clap (CLI) and resvg/usvg (PNG) dependencies, keeping only SVG rendering.

If PNG support is desired later:
```toml
mermaid-rs-renderer = { ..., default-features = false, features = ["png"] }
```

### 4. API Surface

**mermaid-rs-renderer exports** (from `lib.rs`):
- `render(input: &str) -> Result<String>` - Simple one-liner
- `render_with_options(input: &str, options: RenderOptions) -> Result<String>`
- `render_with_timing(input: &str, options: RenderOptions) -> Result<RenderResult>`
- `parse_mermaid(input: &str) -> Result<ParseOutput>` - Low-level
- `compute_layout(...)` - Low-level
- `render_svg(...)` - Low-level
- `Theme`, `LayoutConfig`, `RenderOptions` - Configuration types

**Recommended Python API**:
1. **Simple**: `render(diagram: str) -> str`
2. **With options**: `render(diagram, theme=None, node_spacing=None, rank_spacing=None) -> str`
3. **With timing**: `render_with_timing(diagram) -> tuple[str, int, int, int, int]`
4. **Metadata**: `supported_diagram_types() -> list[str]`

### 5. Error Handling

mermaid-rs-renderer uses `anyhow::Result` for errors. The Python bindings should:
- Convert Rust errors to Python `ValueError` with descriptive messages
- Handle parse errors gracefully (diagram syntax errors)

### 6. Thread Safety

Both projects use `#[pymodule(gil_used = false)]`, allowing GIL-free operation.

mermaid-rs-renderer's render functions are synchronous and stateless, making them naturally thread-safe for the Python bindings.

## Version Matrix

Based on ripgrep_rs reference:

| Component | Version |
|-----------|---------|
| Python | 3.12, 3.13, 3.13t, 3.14, 3.14t |
| Rust | 1.85+ (2024 edition) |
| PyO3 | 0.27 |
| Maturin | >=1.0,<2.0 |

## Build Considerations

### CI Platforms (from ripgrep_rs)
- Linux: x86_64, aarch64 (manylinux)
- macOS: x86_64, aarch64 (Apple Silicon)
- Windows: x64

### Free-threaded Python
The workflows support Python 3.13t and 3.14t (free-threaded) on Linux and macOS, but not Windows (not yet available).

## Potential Issues

### 1. Vendored dagre_rust Dependency

The upstream mermaid-rs-renderer uses:
```toml
[patch.crates-io]
dagre_rust = { path = "vendor/dagre_rust" }
```

When using as a git dependency, this should work. When vendoring, ensure the vendor directory is included.

### 2. Large Parser Module

The `parser.rs` is 209KB - this is fine but may increase compile times.

### 3. PNG Feature Dependencies

If PNG support is enabled, resvg and usvg add significant dependencies. Keep disabled unless needed.

## File Structure

```
python-mermaid-rs/
├── .github/
│   └── workflows/
│       ├── ci.yml          # Test on push/PR
│       └── release.yml     # Build wheels on release
├── mermaid_rs/
│   ├── __init__.py         # Re-exports from native module
│   ├── __init__.pyi        # Type stubs
│   └── py.typed            # PEP 561 marker
├── src/
│   └── lib.rs              # PyO3 bindings
├── tests/
│   ├── __init__.py
│   └── test_mermaid.py
├── Cargo.toml
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

## Next Steps

1. **Test build**: Run `maturin develop` to verify compilation
2. **Handle dagre_rust**: If git dependency fails, vendor the dependency
3. **Add PNG support**: Optional - add `features = ["png"]` and a `render_png()` function
4. **Request crates.io publication**: Contact upstream author
5. **Add more API**: Consider exposing `Theme` customization, `LayoutConfig`, etc.

## Testing the Build

```bash
cd /home/phil65/dev/oss/python-mermaid-rs
python -m venv .venv
source .venv/bin/activate
pip install maturin pytest
maturin develop
python -c "import mermaid_rs; print(mermaid_rs.render('flowchart LR; A-->B')[:100])"
pytest tests/ -v
```

## Upstream Considerations

- **License**: MIT (compatible)
- **Maintenance**: Active (recent commits)
- **Stability**: Version 0.1.2 - API may change
- **Issue**: dagre_rust patching suggests upstream fixes not yet merged
