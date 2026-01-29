"""Core utilities for graph visualization.

This module contains the actual implementation for:
- graph serialization (dict / JSON / NetworkX)
- node/edge filtering for visualization
- color and styling helpers
- PyVis-based 2D web visualization
- summary printing

The public facade for external users remains ``GraphVisualizer`` in
``graph_crawler.shared.utils.visualization`` which delegates to this module.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from graph_crawler.domain.entities.graph import Graph

logger = logging.getLogger(__name__)


def blend_colors(colors: List[str]) -> Optional[str]:
    """Blend multiple HEX colors into a single average color.

    Args:
        colors: List of HEX color strings (e.g. ["#ffffff", "#000000"]).

    Returns:
        HEX color string representing the average color or ``None``
        if the input list is empty.
    """
    if not colors:
        return None
    if len(colors) == 1:
        return colors[0]

    rgb_values: List[Tuple[int, int, int]] = []
    for color in colors:
        color = color.lstrip("#")
        rgb = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))
        rgb_values.append(rgb)

    avg_r = int(sum(r for r, g, b in rgb_values) / len(rgb_values))
    avg_g = int(sum(g for r, g, b in rgb_values) / len(rgb_values))
    avg_b = int(sum(b for r, g, b in rgb_values) / len(rgb_values))

    return f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}"


def graph_to_dict(graph: Graph, include_metadata: bool = True) -> Dict[str, Any]:
    """Export graph to a plain dictionary structure.

    This is optimized with comprehensions and used as the base for
    JSON / NetworkX exports.
    """
    nodes_data = []
    for node in graph.nodes.values():
        node_dict = {
            "id": node.node_id,
            "url": node.url,
            "depth": node.depth,
            "scanned": node.scanned,
            "should_scan": node.should_scan,
            "status": node.response_status,
        }
        # Додаємо всі публічні атрибути для highlight_params
        if hasattr(node, "__dict__"):
            for key, value in node.__dict__.items():
                if not key.startswith("_") and key not in node_dict:
                    # Тільки прості типи для JSON
                    if isinstance(value, (bool, int, float, str, type(None))):
                        node_dict[key] = value
        if include_metadata and getattr(node, "metadata", None):
            node_dict["metadata"] = node.metadata
        nodes_data.append(node_dict)

    edges_data = [
        {
            "source": edge.source_node_id,
            "target": edge.target_node_id,
            **({"metadata": edge.metadata} if getattr(edge, "metadata", None) else {}),
        }
        for edge in graph.edges
    ]

    return {"nodes": nodes_data, "edges": edges_data, "stats": graph.get_stats()}


def graph_to_json(
        graph: Graph,
        filepath: Optional[str] = None,
        include_metadata: bool = True,
) -> str:
    """Export graph to JSON string and optionally persist to file."""
    data = graph_to_dict(graph, include_metadata)
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_str)
    return json_str


def graph_to_networkx(graph: Graph):
    """Convert internal Graph representation to a NetworkX ``DiGraph``.

    Raises:
        ImportError: if ``networkx`` is not installed.
    """
    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover - defensive branch
        raise ImportError("Встановіть networkx: pip install networkx") from exc

    g_nx = nx.DiGraph()
    for node in graph.nodes.values():
        g_nx.add_node(
            node.node_id,
            url=node.url,
            depth=node.depth,
            scanned=node.scanned,
            title=node.get_title() or "",
            label=node.url or "root",
        )
    for edge in graph.edges:
        g_nx.add_edge(edge.source_node_id, edge.target_node_id)
    return g_nx


def filter_nodes_for_visualization(
        graph: Graph,
        max_nodes: int,
        structure_only: bool,
        priority_attributes: Optional[List[str]] = None,
) -> List[Any]:
    """Filter nodes for visualization according to structural settings.

    This logic was previously implemented as a private static method
    on ``GraphVisualizer`` and is now extracted for reuse and testing.
    
    Priority order:
    1. Structural nodes (non-url types)
    2. Nodes with priority attributes (if specified)
    3. Other url nodes
    
    Args:
        graph: Graph to filter
        max_nodes: Maximum number of nodes to visualize
        structure_only: If True, only show structural nodes
        priority_attributes: List of attribute names to prioritize (e.g., ["is_jobs", "is_important"])
    """
    nodes_list = list(graph.nodes.values())
    if structure_only:
        filtered: List[Any] = []
        for node in nodes_list:
            if hasattr(node, "node_type") and node.node_type != "url":
                filtered.append(node)
            elif node.depth == 0:
                filtered.append(node)
        logger.info(" Режим structure_only: %s структурних вузлів", len(filtered))
        return filtered

    if len(nodes_list) > max_nodes:
        structural: List[Any] = []
        priority_nodes: List[Any] = []
        other_url_nodes: List[Any] = []
        
        for node in nodes_list:
            if hasattr(node, "node_type") and node.node_type != "url":
                structural.append(node)
            elif priority_attributes:
                # Перевіряємо чи має нод хоча б один пріоритетний атрибут
                has_priority = False
                for attr in priority_attributes:
                    if hasattr(node, attr) and getattr(node, attr):
                        has_priority = True
                        break
                if has_priority:
                    priority_nodes.append(node)
                else:
                    other_url_nodes.append(node)
            else:
                other_url_nodes.append(node)
        
        # Пріоритет: structural -> priority -> інші
        result: List[Any] = []
        result.extend(structural)
        
        remaining_slots = max_nodes - len(result)
        if remaining_slots > 0:
            result.extend(priority_nodes[:remaining_slots])
        
        remaining_slots = max_nodes - len(result)
        if remaining_slots > 0:
            result.extend(other_url_nodes[:remaining_slots])
        
        if priority_attributes:
            logger.info(" Фільтрація: %s структурних, %s пріоритетних, %s інших -> %s всього",
                       len(structural), len(priority_nodes), len(other_url_nodes), len(result))
        return result[:max_nodes]

    return nodes_list


def get_base_color(scanned: bool, should_scan: bool) -> Tuple[str, str]:
    """Return base color and category label for a node."""
    if scanned and should_scan:
        return "#22C55E", "Scanned + Should Scan"
    if scanned and not should_scan:
        return "#3B82F6", "Scanned + External"
    if not scanned and should_scan:
        return "#EAB308", "Pending Scan"
    return "#9CA3AF", "External (not scanned)"


def get_border_color(
        node_data: Dict[str, Any],
        highlight_params: Optional[Dict[str, str]],
) -> Optional[str]:
    """Determine border color based on provided highlight parameters.

    ``highlight_params`` is a mapping ``{"param_name": "#RRGGBB", ...}``.
    If any of the parameters is truthy on ``node_data``, its color is
    taken into account when blending.
    """
    if not node_data or not highlight_params:
        return None

    active_colors: List[str] = []
    for param, color in highlight_params.items():
        if param in node_data and node_data[param]:
            active_colors.append(color)

    if active_colors:
        return blend_colors(active_colors)
    return None



def _visualize_via_subprocess(
        graph: Graph,
        output_file: str,
        height: str,
        width: str,
        physics_enabled: bool,
        max_nodes: int,
        highlight_params: Optional[Dict[str, str]],
) -> bool:
    """
    Запускає візуалізацію в subprocess з Python 3.12/3.13.

    Returns:
        True якщо успішно, False якщо не вдалося
    """
    import subprocess
    import tempfile
    import os

    # Шукаємо Python 3.12 або 3.13
    import platform

    python_paths = []

    if platform.system() == "Windows":
        # Windows: спочатку py launcher, потім типові шляхи
        python_paths = [
            ["py", "-3.13"],
            ["py", "-3.12"],
            ["py", "-3.11"],
        ]
        # Додаємо типові шляхи встановлення
        import os
        local_app = os.environ.get("LOCALAPPDATA", "")
        if local_app:
            for ver in ["313", "312", "311"]:
                python_paths.append([f"{local_app}\\Programs\\Python\\Python{ver}\\python.exe"])
    else:
        # Linux/Mac
        python_paths = [
            ["python3.13"],
            ["python3.12"],
            ["python3.11"],
            ["/usr/bin/python3.13"],
            ["/usr/bin/python3.12"],
        ]

    python_cmd = None
    for cmd in python_paths:
        try:
            result = subprocess.run(
                cmd + ["--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "3.14" not in result.stdout:
                python_cmd = cmd
                logger.info(f"✅ Знайдено сумісний Python: {result.stdout.strip()}")
                break
        except:
            continue

    if not python_cmd:
        logger.warning("❌ Не знайдено Python 3.12/3.13 для візуалізації")
        return False

    # Перевіряємо чи встановлено pyvis, якщо ні - встановлюємо
    check_pyvis = subprocess.run(
        python_cmd + ["-c", "import pyvis; print('OK')"],
        capture_output=True, text=True, timeout=10
    )

    if "OK" not in check_pyvis.stdout:
        logger.info("📦 Встановлюємо pyvis та networkx...")
        print("📦 Встановлюємо pyvis та networkx для візуалізації...")

        install_result = subprocess.run(
            python_cmd + ["-m", "pip", "install", "pyvis", "networkx", "-q"],
            capture_output=True, text=True, timeout=120
        )

        if install_result.returncode != 0:
            logger.warning(f"❌ Не вдалося встановити pyvis: {install_result.stderr[:200]}")
            return False

        logger.info("✅ pyvis встановлено успішно")
        print("✅ pyvis встановлено успішно")

    # Зберігаємо граф у тимчасовий JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        graph_json = graph_to_json(graph)
        f.write(graph_json)
        temp_json = f.name

    # Скрипт для візуалізації (з правильною кольоровою схемою)
    viz_script = f'''
import json
import sys
try:
    from pyvis.network import Network
except ImportError:
    print("NEED_INSTALL")
    sys.exit(1)

with open(r"{temp_json}", "r", encoding="utf-8") as f:
    data = json.load(f)

net = Network(height="{height}", width="{width}", directed=True)
highlight = {highlight_params or {}}

# Кольорова схема як в оригіналі
def get_base_color(scanned, should_scan):
    if scanned and should_scan:
        return "#22C55E"  # Зелений - Scanned + Should Scan
    if scanned and not should_scan:
        return "#3B82F6"  # Синій - Scanned + External
    if not scanned and should_scan:
        return "#EAB308"  # Жовтий - Pending Scan
    return "#9CA3AF"  # Сірий - External

def blend_colors(colors):
    if not colors:
        return None
    if len(colors) == 1:
        return colors[0]
    rgb_values = []
    for color in colors:
        color = color.lstrip("#")
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        rgb_values.append(rgb)
    avg_r = int(sum(r for r, g, b in rgb_values) / len(rgb_values))
    avg_g = int(sum(g for r, g, b in rgb_values) / len(rgb_values))
    avg_b = int(sum(b for r, g, b in rgb_values) / len(rgb_values))
    return f"#{{avg_r:02x}}{{avg_g:02x}}{{avg_b:02x}}"

# Пріоритизуємо ноди за highlight_params
all_nodes = data.get("nodes", [])
if highlight:
    # Ноди з будь-яким highlight атрибутом мають пріоритет
    priority_nodes = []
    other_nodes = []
    for n in all_nodes:
        has_highlight = any(n.get(param) for param in highlight.keys())
        if has_highlight:
            priority_nodes.append(n)
        else:
            other_nodes.append(n)
    prioritized_nodes = (priority_nodes + other_nodes)[:int({max_nodes})]
else:
    prioritized_nodes = all_nodes[:int({max_nodes})]

node_ids = set()
for node in prioritized_nodes:
    node_id = node.get("id") or node.get("node_id")
    node_ids.add(node_id)
    
    scanned = node.get("scanned", False)
    should_scan = node.get("should_scan", True)
    base_color = get_base_color(scanned, should_scan)
    
    # Визначаємо колір обводки для highlight
    border_color = None
    active_colors = []
    for param, col in highlight.items():
        if node.get(param):
            active_colors.append(col)
    if active_colors:
        border_color = blend_colors(active_colors)
    
    url = node.get("url", "")
    label_text = ''
    if url:
        if len(url) > 80:
            label_text = url[:50] + "..."
        else:
            label_text = url  
    else:
        label_text = str(node_id)[:30]      
    label = label_text
    depth = node.get("depth", 1)
    size = 30 if depth == 0 else 20
    
    # Hover text
    hover = f"<b>URL:</b> {{url}}<br>"
    for param in highlight.keys():
        if param in node:
            val = node[param]
            icon = "✅" if val else "❌"
            hover += f"<b>{{param}}:</b> {{icon}}<br>"
    
    net.add_node(
        node_id,
        label=label,
        title=hover,
        color={{
            "background": base_color,
            "border": border_color if border_color else base_color,
            "highlight": {{
                "background": base_color,
                "border": border_color if border_color else "#333333",
            }},
        }},
        size=size,
        shape="dot" if scanned else "box",
        borderWidth=4 if border_color else 1,
        borderWidthSelected=6 if border_color else 2,
    )

for edge in data.get("edges", []):
    source = edge.get("source") or edge.get("source_id")
    target = edge.get("target") or edge.get("target_id")
    if source in node_ids and target in node_ids:
        net.add_edge(source, target, color="rgba(125, 125, 125, 0.3)", arrows="to")

# Налаштування фізики
physics_opts = """{{
  "physics": {{
    "enabled": {"true" if physics_enabled else "false"},
    "forceAtlas2Based": {{
      "gravitationalConstant": -50,
      "centralGravity": 0.01,
      "springLength": 200,
      "springConstant": 0.08
    }},
    "maxVelocity": 50,
    "solver": "forceAtlas2Based"
  }}
}}"""
net.set_options(physics_opts)
net.save_graph(r"{output_file}")
print("SUCCESS")
'''

    try:
        # Запускаємо subprocess (python_cmd вже список)
        result = subprocess.run(
            python_cmd + ["-c", viz_script],
            capture_output=True, text=True, timeout=60
        )

        if "NEED_INSTALL" in result.stdout:
            logger.warning("pyvis не встановлено в Python 3.12/3.13")
            return False

        if "SUCCESS" in result.stdout:
            logger.info(f"✅ Візуалізацію збережено: {output_file}")
            print(f"✅ Візуалізацію збережено: {output_file}")
            return True

        if result.stderr:
            logger.warning(f"Subprocess error: {result.stderr[:200]}")
        return False

    except subprocess.TimeoutExpired:
        logger.warning("Subprocess timeout")
        return False
    except Exception as e:
        logger.warning(f"Subprocess failed: {e}")
        return False
    finally:
        # Видаляємо тимчасовий файл
        try:
            os.unlink(temp_json)
        except:
            pass


def visualize_2d_web(
        graph: Graph,
        output_file: str = "graph_2d.html",
        height: str = "900px",
        width: str = "100%",
        notebook: bool = False,
        physics_enabled: bool = True,
        max_nodes: int = 1000,
        structure_only: bool = False,
        highlight_params: Optional[Dict[str, str]] = None,
        max_physicist: int = 1000,
        priority_attributes: Optional[List[str]] = None,
) -> None:
    """Create interactive 2D HTML visualization with PyVis.

    This is the core implementation used by
    :meth:`graph_crawler.shared.utils.visualization.GraphVisualizer.visualize_2d_web`.
    
    Args:
        priority_attributes: List of node attributes to prioritize when filtering
                           (e.g., ["is_jobs", "is_important"])
    """
    import sys

    try:
        from pyvis.network import Network
    except ImportError as exc:
        raise ImportError("Встановіть: pip install pyvis") from exc
    except AttributeError as exc:
        # Python 3.14+ несумісність з networkx - спробуємо через subprocess
        if "__annotate__" in str(exc):
            py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
            logger.warning(f"Python {py_ver} несумісний з networkx, спробуємо через subprocess...")

            success = _visualize_via_subprocess(
                graph=graph,
                output_file=output_file,
                height=height,
                width=width,
                physics_enabled=physics_enabled,
                max_nodes=max_nodes,
                highlight_params=highlight_params,
            )
            if success:
                return

            # Якщо subprocess не вдався - виводимо повідомлення
            print(f"\n⚠️ Візуалізація пропущена через несумісність Python {py_ver}")
            print(f"📊 Граф успішно створено: {len(graph.nodes)} вузлів")
            print(f"💡 Встановіть Python 3.12/3.13 для візуалізації")
            return
        raise

    total_nodes = len(graph.nodes)
    logger.info("Початок 2D візуалізації графу: %s вузлів", total_nodes)

    if total_nodes > max_nodes and not structure_only:
        logger.warning(" Граф містить %s вузлів, ліміт %s", total_nodes, max_nodes)
        logger.info(" Візуалізуємо перші %s вузлів", max_nodes)

    nodes_to_visualize = filter_nodes_for_visualization(
        graph, max_nodes, structure_only, priority_attributes
    )
    logger.info(" Візуалізація %s вузлів з %s", len(nodes_to_visualize), total_nodes)

    net = Network(height=height, width=width, directed=True, notebook=notebook)

    # Physics configuration
    if physics_enabled and len(nodes_to_visualize) <= max_physicist:
        net.set_options(
            """
            {
              "physics": {
                "enabled": true,
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "centralGravity": 0.01,
                  "springLength": 200,
                  "springConstant": 0.08
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based"
              }
            }
            """
        )
    else:
        net.set_options(
            """
            {
              "physics": {
                "enabled": false
              },
              "layout": {
                "hierarchical": {
                  "enabled": true,
                  "direction": "UD",
                  "sortMethod": "directed"
                }
              }
            }
            """
        )
        if len(nodes_to_visualize) > max_physicist:
            logger.info("ℹ Фізика вимкнена для оптимізації")

    node_ids = {node.node_id for node in nodes_to_visualize}

    for node in nodes_to_visualize:
        # Collect public attributes for hover/highlight logic
        node_data: Dict[str, Any] = {}
        if hasattr(node, "__dict__"):
            for key, value in node.__dict__.items():
                if not key.startswith("_"):
                    node_data[key] = value

        base_color, _category = get_base_color(node.scanned, node.should_scan)

        border_color: Optional[str] = None
        if highlight_params:
            border_color = get_border_color(node_data, highlight_params)

        hover_text = f"<b>URL:</b> {node.url}<br>"
        if highlight_params:
            for param in highlight_params.keys():
                if param in node_data:
                    value = node_data[param]
                    icon = "" if value else ""
                    hover_text += f"<b>{param}:</b> {icon}<br>"

        label = str(node.url)[:50] or "root"
        size = 30 if node.depth == 0 else 20

        node_config: Dict[str, Any] = {
            "label": label,
            "title": hover_text,
            "color": {
                "background": base_color,
                "border": border_color if border_color else base_color,
                "highlight": {
                    "background": base_color,
                    "border": border_color if border_color else "#333333",
                },
            },
            "size": size,
            "shape": "dot" if node.scanned else "box",
            "borderWidth": 4 if border_color else 1,
            "borderWidthSelected": 6 if border_color else 2,
        }

        net.add_node(node.node_id, **node_config)

    # Add edges
    edges_added = 0
    for edge in graph.edges:
        if edge.source_node_id in node_ids and edge.target_node_id in node_ids:
            net.add_edge(
                edge.source_node_id,
                edge.target_node_id,
                color="rgba(125, 125, 125, 0.3)",
                arrows="to",
            )
            edges_added += 1
    logger.info(" Додано %s ребер", edges_added)

    net.save_graph(output_file)
    logger.info("2D граф збережено: %s", output_file)


def print_summary(graph: Graph) -> None:
    """Log a human-readable summary about the graph structure."""
    separator = "=" * 60
    logger.info("\n%s", separator)
    logger.info(" ІНФОРМАЦІЯ ПРО ГРАФ")
    logger.info("%s", separator)

    stats = graph.get_stats()
    logger.info("   Всього вузлів: %s", stats["total_nodes"])
    logger.info("   Просканованих: %s", stats["scanned_nodes"])
    logger.info("   Непросканованих: %s", stats["unscanned_nodes"])
    logger.info("   Всього ребер: %s", stats["total_edges"])

    depths: Dict[int, int] = {}
    for node in graph.nodes.values():
        depths[node.depth] = depths.get(node.depth, 0) + 1

    for depth in sorted(depths.keys()):
        logger.info("   Depth %s: %s вузлів", depth, depths[depth])

    logger.info("\n%s", separator)
