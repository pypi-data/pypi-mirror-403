import re
import sys
import xml.etree.ElementTree as ET

class Flowmaid:
  """
  Flowmaid: A pure Python library to convert Mermaid flowcharts to SVG.
  """
  def __init__(self, mermaid_code):
    self.mermaid_code = mermaid_code
    self.direction = "TD"
    self.nodes = {}
    self.edges = []
    self.subgraphs = {}
    self.link_styles = {}
    self._parse()

  def _parse(self):
    lines = self.mermaid_code.strip().split('\n')
    current_subgraph = None
    for line in lines:
      line = line.strip()
      if not line or line.startswith('%%'):
        continue
      
      # Handle subgraphs
      subgraph_match = re.match(r'^subgraph\s+(\w+)(?:\[(.*)\])?', line)
      if subgraph_match:
        sg_id = subgraph_match.group(1)
        sg_label = subgraph_match.group(2) or sg_id
        current_subgraph = sg_id
        self.subgraphs[sg_id] = {'id': sg_id, 'label': sg_label, 'nodes': []}
        continue
      if line == 'end' and current_subgraph:
        current_subgraph = None
        continue

      # Handle styles (basic: extract color and stroke)
      # style A fill:#f9f,stroke:#333,stroke-width:4px
      style_match = re.match(r'^style\s+(\w+)\s+(.*)', line)
      if style_match:
        node_id = style_match.group(1)
        styles = style_match.group(2)
        style_dict = {}
        for s in styles.split(','):
          if ':' in s:
            k, v = s.split(':', 1)
            style_dict[k.strip()] = v.strip()
        if node_id in self.nodes:
          self.nodes[node_id]['style'] = style_dict
        else:
          # Pre-define node style if node hasn't been seen yet
          self.nodes[node_id] = {'id': node_id, 'label': node_id, 'shape': 'rect', 'style': style_dict, 'subgraph_id': current_subgraph}
        continue

      # Handle linkStyle
      # linkStyle 0 stroke:#ff3,stroke-width:4px
      ls_match = re.match(r'^linkStyle\s+(\d+)\s+(.*)', line)
      if ls_match:
        index = int(ls_match.group(1))
        styles = ls_match.group(2)
        style_dict = {}
        for s in styles.split(','):
          if ':' in s:
            k, v = s.split(':', 1)
            style_dict[k.strip()] = v.strip()
        self.link_styles[index] = style_dict
        continue

      # Parse graph header
      header_match = re.match(r'^(graph|flowchart)\s+(TD|BT|LR|RL|TB)', line, re.I)
      if header_match:
        self.direction = header_match.group(2).upper()
        if self.direction == 'TB': self.direction = 'TD'
        continue

      # Parse edges and nodes
      # Handling transitions: A -- label --> B or A --> B or A -- label --- B or A --- B
      # Also handling chained transitions: A --> B --> C
      # Complex edge patterns: ==> (thick), -.-> (dotted)
      edge_pattern = r'(--(?:.*?)--?>|--?>|---(?:.*?)---|---|==(?:.*?)==>|==>|-\.(?:.*?)\.->|-\.->)'
      if re.search(r'-->\|.*?\|', line):
        line = re.sub(r'-->\|(.*?)\|', r'--\1-->', line)
      
      if re.search(edge_pattern, line):
        # Split by edge pattern but keep the edges to know the type/label
        parts = re.split(edge_pattern, line)
        # parts will be [node, edge, node, edge, node...]
        prev_node_id = None
        for i in range(0, len(parts), 2):
          node_part = parts[i].strip()
          if not node_part: continue
          
          # Remove trailing semicolon
          if node_part.endswith(';'): node_part = node_part[:-1].strip()

          node_id, label, shape = self._parse_node_def(node_part)
          if node_id:
            if node_id not in self.nodes:
              self.nodes[node_id] = {'id': node_id, 'label': label, 'shape': shape, 'subgraph_id': current_subgraph}
            else:
              # Update subgraph_id if it was previously unknown
              if current_subgraph:
                self.nodes[node_id]['subgraph_id'] = current_subgraph
            
            if current_subgraph:
              if node_id not in self.subgraphs[current_subgraph]['nodes']:
                self.subgraphs[current_subgraph]['nodes'].append(node_id)
            
            if prev_node_id and i > 0:
              edge_type_part = parts[i-1]
              edge_label = ""
              # Extract label from --label--> or --label--- or ==label==> or -.label.->
              label_match = re.search(r'-+(.*?)-+>?|==+(.*?)==+>|-\.(.*?)\.->', edge_type_part)
              if label_match:
                edge_label = (label_match.group(1) or label_match.group(2) or label_match.group(3) or "").strip()
              
              style = 'normal'
              if '==' in edge_type_part: style = 'thick'
              elif '-.' in edge_type_part: style = 'dotted'

              self.edges.append({
                'from': prev_node_id,
                'to': node_id,
                'label': edge_label,
                'arrow': '>' in edge_type_part,
                'style': style
              })
            prev_node_id = node_id
      else:
        # Check for node with label containing special chars
        if line.endswith(';'): line = line[:-1].strip()
        node_id, label, shape = self._parse_node_def(line)
        if node_id:
          if node_id not in self.nodes:
            self.nodes[node_id] = {'id': node_id, 'label': label, 'shape': shape, 'subgraph_id': current_subgraph}
          else:
            if current_subgraph:
              self.nodes[node_id]['subgraph_id'] = current_subgraph
          if current_subgraph:
            if node_id not in self.subgraphs[current_subgraph]['nodes']:
              self.subgraphs[current_subgraph]['nodes'].append(node_id)

  def _parse_node_def(self, text):
    text = text.strip()
    if not text: return None, None, None

    # Node shapes:
    # Circle: A((text))
    m = re.match(r'^(\w+)\(\((.*)\)\)$', text)
    if m: return m.group(1), m.group(2), 'circle'
    # Cylinder: A[(text)]
    m = re.match(r'^(\w+)\[\((.*)\)\]$', text)
    if m: return m.group(1), m.group(2), 'cylinder'
    # Rectangular: A[text]
    m = re.match(r'^(\w+)\[(.*)\]$', text)
    if m: return m.group(1), m.group(2), 'rect'
    # Rounded: A(text)
    m = re.match(r'^(\w+)\((.*)\)$', text)
    if m: return m.group(1), m.group(2), 'rounded'
    # Diamond: A{text}
    m = re.match(r'^(\w+)\{(.*)\}$', text)
    if m: return m.group(1), m.group(2), 'diamond'
    # Rhomboid: A>text]
    m = re.match(r'^(\w+)>(.*)\]$', text)
    if m: return m.group(1), m.group(2), 'rhomboid'
    
    # Just ID: A
    m = re.match(r'^(\w+)$', text)
    if m: return m.group(1), m.group(1), 'rect'
    
    return None, None, None

  def generate_svg(self):
    # Dynamic node sizing with text wrapping
    def get_node_size(label):
      char_width = 8.5
      max_width = 200
      padding = 20
      
      lines = []
      words = label.split(' ')
      current_line = ""
      for word in words:
        if (len(current_line) + len(word) + 1) * char_width < max_width:
          current_line += (" " if current_line else "") + word
        else:
          if current_line: lines.append(current_line)
          current_line = word
      if current_line: lines.append(current_line)
      
      if not lines: lines = [""]
      
      w = max(100, max(len(l) for l in lines) * char_width + padding)
      h = len(lines) * 20 + padding
      return w, h, lines

    node_data = {node_id: get_node_size(node['label']) for node_id, node in self.nodes.items()}
    node_sizes = {node_id: (d[0], d[1]) for node_id, d in node_data.items()}
    node_lines = {node_id: d[2] for node_id, d in node_data.items()}
    
    h_spacing = 60
    v_spacing = 80
    
    # Simple layout
    layout = {}
    all_nodes = list(self.nodes.keys())
    if not all_nodes:
      return ET.tostring(ET.Element('svg'), encoding='unicode')

    # BFS-based ranking
    ranks = {node_id: 0 for node_id in all_nodes}
    
    to_nodes = set(e['to'] for e in self.edges)
    roots = [n for n in all_nodes if n not in to_nodes]
    if not roots: roots = [all_nodes[0]]

    from collections import deque
    queue = deque([(root, 0) for root in roots])
    visited = set(roots)

    while queue:
      u, r = queue.popleft()
      ranks[u] = r
      for edge in self.edges:
        if edge['from'] == u and edge['to'] not in visited:
          visited.add(edge['to'])
          queue.append((edge['to'], r + 1))
    
    # Handle unreachable nodes
    for node_id in all_nodes:
      if node_id not in visited:
        ranks[node_id] = 0
        visited.add(node_id)

    # Calculate positions with varying sizes
    if self.direction in ['TD', 'TB']:
      rank_y = {}
      current_y = 60
      max_ranks = max(ranks.values()) if ranks else 0
      for r in range(max_ranks + 1):
        rank_nodes = [n for n in all_nodes if ranks[n] == r]
        if not rank_nodes: continue
        # Sort nodes by subgraph_id to group them horizontally
        rank_nodes.sort(key=lambda n: (self.nodes[n].get('subgraph_id') or "", n))
        
        max_h = max((node_sizes[n][1] for n in rank_nodes), default=40)
        rank_y[r] = current_y
        
        current_x = 60
        for n in rank_nodes:
          nw, nh = node_sizes[n]
          layout[n] = (current_x, current_y + (max_h - nh) / 2)
          current_x += nw + h_spacing
        current_y += max_h + v_spacing
    else:
      rank_x = {}
      current_x = 60
      max_ranks = max(ranks.values()) if ranks else 0
      for r in range(max_ranks + 1):
        rank_nodes = [n for n in all_nodes if ranks[n] == r]
        if not rank_nodes: continue
        # Sort nodes by subgraph_id to group them vertically
        rank_nodes.sort(key=lambda n: (self.nodes[n].get('subgraph_id') or "", n))
        
        max_w = max((node_sizes[n][0] for n in rank_nodes), default=120)
        rank_x[r] = current_x
        
        current_y = 60
        for n in rank_nodes:
          nw, nh = node_sizes[n]
          layout[n] = (current_x + (max_w - nw) / 2, current_y)
          current_y += nh + v_spacing
        current_x += max_w + h_spacing

    # Calculate viewBox size - initial pass
    max_x = max((layout[n][0] + node_sizes[n][0] for n in all_nodes), default=400) + 60
    max_y = max((layout[n][1] + node_sizes[n][1] for n in all_nodes), default=400) + 60

    # Draw subgraphs first to get their bounds
    subgraph_els = []
    for sg_id, sg in self.subgraphs.items():
      if not sg['nodes']: continue
      
      sg_node_positions = []
      for n_id in sg['nodes']:
        if n_id in layout:
          nw, nh = node_sizes[n_id]
          px, py = layout[n_id]
          sg_node_positions.append((px, py, nw, nh))
          
      if not sg_node_positions: continue
      
      min_x_sg = min(p[0] for p in sg_node_positions) - 20
      min_y_sg = min(p[1] for p in sg_node_positions) - 40
      max_x_sg = max(p[0] + p[2] for p in sg_node_positions) + 20
      max_y_sg = max(p[1] + p[3] for p in sg_node_positions) + 20
      
      max_x = max(max_x, max_x_sg + 20)
      max_y = max(max_y, max_y_sg + 20)
      
      subgraph_els.append((sg_id, sg['label'], min_x_sg, min_y_sg, max_x_sg, max_y_sg))

    svg = ET.Element('svg', {
      'xmlns': 'http://www.w3.org/2000/svg',
      'width': str(max_x),
      'height': str(max_y),
      'viewBox': f'0 0 {max_x} {max_y}'
    })
    
    # Styles
    style = ET.SubElement(svg, 'style')
    style.text = """
      .edge path { fill: none; stroke: #333; stroke-width: 1.5px; }
      .edge path.thick { stroke-width: 3.5px; }
      .edge path.dotted { stroke-dasharray: 3; }
      .edge-label { font-size: 10px; fill: #333; }
      .subgraph rect { stroke-dasharray: 0; }
      text { font-family: 'trebuchet ms', verdana, arial, sans-serif; font-size: 14px; }
      .arrowhead { fill: #333; }
    """

    # Marker for arrowheads
    defs = ET.SubElement(svg, 'defs')
    marker = ET.SubElement(defs, 'marker', {
      'id': 'arrowhead',
      'markerWidth': '10',
      'markerHeight': '7',
      'refX': '10',
      'refY': '3.5',
      'orient': 'auto'
    })
    ET.SubElement(marker, 'polygon', {
      'points': '0 0, 10 3.5, 0 7',
      'class': 'arrowhead'
    })

    # Draw subgraphs
    for sg_id, label, min_x, min_y, max_x_sg, max_y_sg in subgraph_els:
      g_sg = ET.SubElement(svg, 'g', {'class': 'subgraph', 'id': sg_id})
      ET.SubElement(g_sg, 'rect', {
        'x': str(min_x), 'y': str(min_y),
        'width': str(max_x_sg - min_x), 'height': str(max_y_sg - min_y),
        'fill': '#f9f9f9', 'stroke': '#333', 'stroke-width': '1px', 'rx': '5'
      })
      label_bg = ET.SubElement(g_sg, 'rect', {
        'x': str(min_x), 'y': str(min_y),
        'width': str(max_x_sg - min_x), 'height': '25',
        'fill': '#eee', 'stroke': '#333', 'stroke-width': '1px', 'rx': '5'
      })
      label_text = ET.SubElement(g_sg, 'text', {
        'x': str((min_x + max_x_sg) / 2), 'y': str(min_y + 17),
        'text-anchor': 'middle', 'font-weight': 'bold'
      })
      label_text.text = label

    # Draw edges
    for i, edge in enumerate(self.edges):
      start_pos = layout[edge['from']]
      end_pos = layout[edge['to']]
      snw, snh = node_sizes[edge['from']]
      enw, enh = node_sizes[edge['to']]
      
      x1, y1 = start_pos[0] + snw / 2, start_pos[1] + snh / 2
      x2, y2 = end_pos[0] + enw / 2, end_pos[1] + enh / 2
      
      dx = x2 - x1
      dy = y2 - y1
      
      def get_boundary_intersection(x, y, w, h, dx, dy, shape):
        if dx == 0 and dy == 0: return x, y
        if shape == 'circle':
          dist = (dx*dx + dy*dy)**0.5
          return x + (dx/dist) * (w/2), y + (dy/dist) * (h/2)
        elif shape == 'diamond':
          abs_dx, abs_dy = abs(dx), abs(dy)
          hw, hh = w/2, h/2
          if abs_dx == 0: return x, y + (hh if dy > 0 else -hh)
          if abs_dy == 0: return x + (hw if dx > 0 else -hw), y
          ix = (hw * hh) / (hh + hw * abs_dy / abs_dx)
          return x + (ix if dx > 0 else -ix), y + (ix * abs_dy / abs_dx if dy > 0 else -ix * abs_dy / abs_dx)
        else: # rect, rounded, cylinder, rhomboid
          abs_dx, abs_dy = abs(dx), abs(dy)
          hw, hh = w/2, h/2
          if abs_dx == 0: return x, y + (hh if dy > 0 else -hh)
          if abs_dy == 0: return x + (hw if dx > 0 else -hw), y
          if abs_dy * hw > abs_dx * hh:
            return x + (hh * abs_dx / abs_dy if dx > 0 else -hh * abs_dx / abs_dy), y + (hh if dy > 0 else -hh)
          else:
            return x + (hw if dx > 0 else -hw), y + (hw * abs_dy / abs_dx if dy > 0 else -hw * abs_dy / abs_dx)

      from_node = self.nodes[edge['from']]
      to_node = self.nodes[edge['to']]
      sx, sy = get_boundary_intersection(x1, y1, snw, snh, dx, dy, from_node['shape'])
      ex, ey = get_boundary_intersection(x2, y2, enw, enh, -dx, -dy, to_node['shape'])

      g_edge = ET.SubElement(svg, 'g', {'class': 'edge'})
      path_data = f"M {sx} {sy} L {ex} {ey}"
      path_class = 'edge-path'
      if edge.get('style') == 'thick': path_class += ' thick'
      elif edge.get('style') == 'dotted': path_class += ' dotted'
      
      path_attrs = {'d': path_data, 'class': path_class}
      
      # Apply linkStyle
      if i in self.link_styles:
        ls = self.link_styles[i]
        path_style = ""
        for k, v in ls.items():
          path_style += f"{k}:{v};"
        path_attrs['style'] = path_style

      if edge['arrow']:
        path_attrs['marker-end'] = 'url(#arrowhead)'
      ET.SubElement(g_edge, 'path', path_attrs)
      
      if edge['label']:
        lx, ly = (sx + ex) / 2, (sy + ey) / 2
        label_text = ET.SubElement(g_edge, 'text', {
          'x': str(lx),
          'y': str(ly - 5),
          'class': 'edge-label',
          'text-anchor': 'middle'
        })
        label_text.text = edge['label']

    # Draw nodes
    for node_id, node in self.nodes.items():
      x, y = layout[node_id]
      nw, nh = node_sizes[node_id]
      node_style = node.get('style', {})
      fill = node_style.get('fill', '#ececff')
      stroke = node_style.get('stroke', '#9370db')
      stroke_width = node_style.get('stroke-width', '1px')
      
      g_node = ET.SubElement(svg, 'g', {'class': 'node', 'id': node_id})
      common_attrs = {'fill': fill, 'stroke': stroke, 'stroke-width': stroke_width}
      
      if node['shape'] == 'circle':
        attrs = {
          'cx': str(x + nw/2),
          'cy': str(y + nh/2),
          'rx': str(nw/2),
          'ry': str(nh/2)
        }
        attrs.update(common_attrs)
        ET.SubElement(g_node, 'ellipse', attrs)
      elif node['shape'] == 'diamond':
        hw, hh = nw/2, nh/2
        cx, cy = x + hw, y + hh
        points = f"{cx},{y} {x+nw},{cy} {cx},{y+nh} {x},{cy}"
        attrs = {'points': points}
        attrs.update(common_attrs)
        ET.SubElement(g_node, 'polygon', attrs)
      elif node['shape'] == 'rounded':
        attrs = {
          'x': str(x), 'y': str(y),
          'width': str(nw), 'height': str(nh),
          'rx': '10', 'ry': '10'
        }
        attrs.update(common_attrs)
        ET.SubElement(g_node, 'rect', attrs)
      elif node['shape'] == 'cylinder':
        cx, cy = x + nw/2, y + nh/2
        rx, ry = nw/2, 5
        path_data = f"M {x} {y+ry} a {rx} {ry} 0 1 0 {nw} 0 a {rx} {ry} 0 1 0 -{nw} 0 v {nh-2*ry} a {rx} {ry} 0 0 0 {nw} 0 v -{nh-2*ry}"
        attrs = {'d': path_data}
        attrs.update(common_attrs)
        ET.SubElement(g_node, 'path', attrs)
      elif node['shape'] == 'rhomboid':
        off = 20
        points = f"{x+off},{y} {x+nw},{y} {x+nw-off},{y+nh} {x},{y+nh}"
        attrs = {'points': points}
        attrs.update(common_attrs)
        ET.SubElement(g_node, 'polygon', attrs)
      else: # rect
        attrs = {
          'x': str(x), 'y': str(y),
          'width': str(nw), 'height': str(nh)
        }
        attrs.update(common_attrs)
        ET.SubElement(g_node, 'rect', attrs)
      
      text_el = ET.SubElement(g_node, 'text', {
        'x': str(x + nw/2),
        'y': str(y + nh/2 + 5),
        'text-anchor': 'middle'
      })
      lines = node_lines[node_id]
      if len(lines) == 1:
        text_el.text = lines[0]
      else:
        # For multi-line text, we need to adjust the y position
        total_height = len(lines) * 20
        start_y = y + (nh - total_height) / 2 + 15
        for i, line in enumerate(lines):
          tspan = ET.SubElement(text_el, 'tspan', {
            'x': str(x + nw/2),
            'dy': '0' if i == 0 else '20'
          })
          if i == 0:
            tspan.set('y', str(start_y))
          tspan.text = line

    return ET.tostring(svg, encoding='unicode')

def main():
  if len(sys.argv) < 2:
    print("Usage: python Flowmaid.py <mermaid_file>")
    return
  
  try:
    with open(sys.argv[1], 'r') as f:
      code = f.read()
    mp = Flowmaid(code)
    print(mp.generate_svg())
  except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
  main()
