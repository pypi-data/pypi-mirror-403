# Flowmaid.py

**Flowmaid.py** is a pure Python library designed to convert Mermaid flowcharts into clean, styled SVG files. It serves as a lightweight, zero-dependency alternative to the JavaScript-based `mermaid.js` for flowchart rendering.

## Features

- **Zero Dependencies:** Uses only the Python standard library.
- **Single File:** The entire library is contained in `Flowmaid.py`.
- **Mermaid Syntax Support:**
  - `graph` and `flowchart` headers.
  - Directions: `TD` (Top-Down) and `LR` (Left-Right).
  - Node Shapes: Rectangular `[]`, Rounded `()`, Diamond `{}`, Circle `(())`, Cylinder `[()]`, and Rhomboid `>]`.
  - Edge Types: Normal `-->`, Thick `==>`, Dotted `-.->`, and Link `---`.
  - Labeled Edges: `A -- label --> B` or `A -->|label| B`.
- **Advanced Styling:**
  - `style` command for node colors, borders, and widths.
  - `linkStyle` command for individual edge customization.
- **Subgraphs:** Support for `subgraph` blocks with custom labels and visual grouping.
- **Layout & Rendering:**
  - BFS-based hierarchical ranking for stable positioning.
  - Dynamic node sizing based on label length.
  - Automatic text wrapping for long labels.
  - Precise arrowheads that point exactly to node boundaries.

## Installation

Simply copy `Flowmaid.py` into your project. No `pip install` required!

## Usage

### Command Line

You can generate an SVG directly from a Mermaid file:

```bash
python3 Flowmaid.py flowchart.mermaid > flowchart.svg
```

### Python API

You can also use Flowmaid.py within your Python scripts:

```python
from Flowmaid import Flowmaid

mermaid_code = """
graph TD
    subgraph SG1[Main Process]
        A[Start] --> B{Is it working?}
        B -- Yes --> C[Great!]
        B -- No --> D[Fix it]
    end
    C --> E[End]
    D --> B
    style A fill:#f9f,stroke:#333,stroke-width:4px
    linkStyle 0 stroke:#ff3,stroke-width:4px
"""

mp = Flowmaid(mermaid_code)
svg_output = mp.generate_svg()

with open("output.svg", "w") as f:
    f.write(svg_output)
```

## Example Output

The library handles complex layouts and ensures that styles are correctly applied as inline SVG attributes for maximum compatibility across different viewers.

## Future Plans

- Support for nested subgraphs.
- Multi-directional edges (`<-->`).
- Support for other Mermaid diagram types (Sequence, Gantt, etc.).
- Improved edge routing to minimize crossovers.
