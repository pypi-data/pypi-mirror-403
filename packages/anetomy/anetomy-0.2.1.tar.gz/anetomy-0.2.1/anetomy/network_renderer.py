from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional

from graphviz import Digraph
from flask import Flask, jsonify, render_template, request


@dataclass
class GraphNode:
    node_id: str
    label: str
    kind: str
    scope: List[str] = field(default_factory=list)
    color: str = "#FFFFFF"
    border: str = "#CC66FF"
    shape: str = "box"


@dataclass
class GraphEdge:
    src: str
    dst: str
    label: str


class NetGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, GraphNode] = {}
        self._edge_counts: Dict[tuple, int] = {}
        self._op_counts: Dict[str, int] = {}
        self._io_count = 0
        self.clusters: Dict[str, str] = {}
        self.root_id = ""
        self.module_repeats: Dict[str, int] = {}
        self.root_is_leaf = False

    def add_root(self, label: str) -> str:
        node_id = "root_0"
        self.nodes[node_id] = GraphNode(
            node_id=node_id,
            label=label,
            kind="root",
            color="#FF3333",
            border="#FF3333",
            shape="box",
        )
        self.root_id = node_id
        return node_id

    def add_op(self, base_name: str, label: str, scope: List[str], color: str, border: str) -> str:
        count = self._op_counts.get(base_name, 0)
        self._op_counts[base_name] = count + 1
        safe_base = re.sub(r"[^a-zA-Z0-9_]", "_", base_name)
        node_id = f"op_{safe_base}_{count}"
        self.nodes[node_id] = GraphNode(
            node_id=node_id,
            label=label,
            kind="op",
            scope=scope,
            color=color,
            border=border,
            shape="box",
        )
        return node_id

    def add_io(self, label: str) -> str:
        self._io_count += 1
        node_id = f"io_{self._io_count}"
        self.nodes[node_id] = GraphNode(
            node_id=node_id,
            label=label,
            kind="io",
            color="#CC66FF",
            border="#CC66FF",
            shape="box",
        )
        return node_id

    def add_edge(self, src: str, dst: str, label: str) -> None:
        key = (src, dst, label)
        self._edge_counts[key] = self._edge_counts.get(key, 0) + 1

    def set_cluster_label(self, scope_path: str, label: str, repeat_count: Optional[int] = None) -> None:
        self.clusters[scope_path] = label
        if repeat_count is not None:
            self.module_repeats[scope_path] = repeat_count

    def iter_edges(self) -> List[GraphEdge]:
        grouped = {}
        for (src, dst, label), count in self._edge_counts.items():
            grouped.setdefault((src, dst), []).append((label, count))
        edges = []
        for (src, dst), entries in grouped.items():
            parts = []
            for label, count in entries:
                if count > 1:
                    if label:
                        parts.append(f"{label}\n [ x{count} ]")
                    else:
                        parts.append(f" [ x{count} ]")
                else:
                    parts.append(label or "")
            merged = "\n".join(p for p in parts if p)
            edges.append(GraphEdge(src=src, dst=dst, label=merged))
        return edges

    def max_scope_depth(self) -> int:
        max_depth = 0
        for node in self.nodes.values():
            if node.kind != "op":
                continue
            max_depth = max(max_depth, len(node.scope))
        return max_depth




class Renderer:
    def __init__(self, graph_path: str, export_format: str) -> None:
        self.graph_path = graph_path[:-4]
        self.export_format = export_format
        self.app = Flask(__name__, static_folder="static", template_folder="templates")
        self._setup_routes()
        self.graph = None
        self.graph_data: Optional[NetGraph] = None
        self.graph_stack: Dict[str, Digraph] = {}
        self.graph_parents: Dict[str, str] = {}
        self.rendered_nodes: List[str] = []
        self.max_depth = 0
        self.expand_scopes = set()
        self.collapse_scopes = set()
        self.cluster_map: Dict[str, str] = {}
        self.proxy_id_to_scope: Dict[str, str] = {}
        self.node_display_names: Dict[str, str] = {}
        self._collapsed_top_scope = ""

    def _setup_routes(self) -> None:
        @self.app.route("/")
        def display_graph():
            self.draw(self.max_depth)
            svg_data = self.graph.pipe(format="svg").decode("utf-8")
            return render_template("graph.html", svg_data=svg_data)

        @self.app.route("/refresh", methods=["POST"])
        def refresh():
            data = request.get_json() or {}
            element_type = data.get("type")
            element_id = data.get("id")
            def _toggle_scope(scope_path: str) -> None:
                if scope_path in self.collapse_scopes:
                    self.collapse_scopes.discard(scope_path)
                    return
                if scope_path in self.expand_scopes:
                    self.expand_scopes.discard(scope_path)
                    return
                scope_depth = 0 if not scope_path else scope_path.count("/") + 1
                current_visible = self._visible_depth_for_scope(scope_path)
                if current_visible >= scope_depth:
                    self.collapse_scopes.add(scope_path)
                else:
                    self.expand_scopes.add(scope_path)
            if element_type == "node" and element_id and self.graph_data:
                scope_path = ""
                should_toggle = False
                node = self.graph_data.nodes.get(element_id)
                if node and node.kind == "root":
                    scope_path = ""
                    should_toggle = True
                elif element_id in self.proxy_id_to_scope:
                    scope_path = self.proxy_id_to_scope[element_id]
                    should_toggle = True
                if should_toggle:
                    if scope_path == "":
                        if scope_path in self.expand_scopes:
                            self.expand_scopes.discard(scope_path)
                        else:
                            self.expand_scopes.add(scope_path)
                    else:
                        _toggle_scope(scope_path)
            if element_type == "subgraph" and element_id:
                scope_path = self.cluster_map.get(element_id, "")
                if scope_path and "" in self.expand_scopes and scope_path.count("/") == 0:
                    self.expand_scopes.discard("")
                elif scope_path:
                    _toggle_scope(scope_path)
            self.draw(self.max_depth)
            svg_data = self.graph.pipe(format="svg").decode("utf-8")
            return jsonify({"message": "Refreshed graph", "svg_data": svg_data})

        @self.app.route("/set_depth", methods=["POST"])
        def set_depth():
            data = request.get_json() or {}
            max_depth = data.get("max_depth")
            if not isinstance(max_depth, int) or max_depth < -1:
                return jsonify({"error": "Invalid max depth"}), 400
            self.expand_scopes = set()
            self.collapse_scopes = set()
            self.draw(max_depth)
            svg_data = self.graph.pipe(format="svg").decode("utf-8")
            return jsonify({"message": f"Set max depth to {max_depth}", "svg_data": svg_data})

        @self.app.route("/export", methods=["POST"])
        def export():
            data = request.get_json() or {}
            fmt = data.get("format")
            if fmt not in ["png", "svg"]:
                return jsonify({"error": "Invalid format"}), 400
            self.export_format = fmt
            self.export()
            svg_data = self.graph.pipe(format="svg").decode("utf-8")
            return jsonify({"message": f"Exported to {self.graph_path + '.' + self.export_format}", "svg_data": svg_data})

        @self.app.route("/search", methods=["POST"])
        def search():
            data = request.get_json() or {}
            query = data.get("query", "").lower()
            results = []
            seen = set()
            for node_id in self.rendered_nodes:
                display_name = self.node_display_names.get(node_id, node_id)
                if display_name != node_id:
                    match = query in display_name.lower()
                else:
                    match = query in node_id.lower()
                if match and node_id not in seen:
                    results.append({"type": "node", "id": node_id, "display_name": display_name})
                    seen.add(node_id)
            for scope_id in self.graph_stack.keys():
                if scope_id and query in scope_id.lower() and scope_id not in seen:
                    results.append({"type": "subgraph", "id": scope_id, "display_name": "<G> " + scope_id})
                    seen.add(scope_id)
            return jsonify({"results": results})

        @self.app.route("/center", methods=["POST"])
        def center():
            data = request.get_json() or {}
            type_selected = data.get("type")
            id_selected = data.get("id")
            if type_selected == "node" and id_selected not in self.rendered_nodes:
                return jsonify({"error": f"Node {id_selected} not found"}), 404
            if type_selected == "subgraph" and id_selected not in self.graph_stack:
                return jsonify({"error": f"Subgraph {id_selected} not found"}), 404
            svg_data = self.graph.pipe(format="svg").decode("utf-8")
            return jsonify({"message": "Centered", "svg_data": svg_data})

    def launch(self, host: str, port: int) -> None:
        self.app.run(host=host, port=port, debug=False)

    def draw(self, max_depth: int, graph: Optional[NetGraph] = None) -> None:
        self.max_depth = max_depth
        if graph is None:
            graph = self.graph_data
        if graph is None:
            return
        if self.max_depth < 0:
            self.max_depth = graph.max_scope_depth()
        expanded_root = "" in self.expand_scopes
        collapsed_root = "" in self.collapse_scopes
        top_collapsed = sorted(scope for scope in self.collapse_scopes if scope and "/" not in scope)
        collapsed_top_scope = top_collapsed[0] if len(top_collapsed) == 1 else ""
        self._collapsed_top_scope = collapsed_top_scope
        self.effective_depth = self.max_depth + (1 if expanded_root else 0)
        self.graph = Digraph(format="svg")
        self.graph.attr(rankdir="TB", bgcolor="white", compound="true", outputorder="edgesfirst")
        self.graph.attr("node", fontname="Helvetica")
        self.graph.attr("edge", color="#333333", fontname="Helvetica", fontsize="10")
        self.graph_stack = {"": self.graph}
        self.graph_parents = {}
        self.cluster_map = {}
        self.rendered_nodes = []
        self.node_display_names = {}

        proxy_nodes: Dict[str, GraphNode] = {}
        proxy_ids: Dict[str, str] = {}
        proxy_id_to_scope: Dict[str, str] = {}

        def _is_expanded(scope_path: str) -> bool:
            return scope_path in self.expand_scopes

        def _proxy_for(scope: List[str]) -> str:
            scope_path = "/".join(scope)
            if scope_path in proxy_ids:
                return proxy_ids[scope_path]
            safe = re.sub(r"[^a-zA-Z0-9_]", "_", scope_path)
            node_id = f"proxy_{safe}"
            label = scope[-1]
            if self.graph_data and scope_path in self.graph_data.clusters:
                label = self.graph_data.clusters[scope_path]
            label = f"""<
                        <table border="0" cellborder="0" cellpadding="3" bgcolor="white">
                            <tr>
                                <td bgcolor="black" align="center" colspan="2"><font color="white">{label} D@{len(scope)}</font></td>
                            </tr>
                        </table>
                    >"""
            proxy = GraphNode(
                node_id=node_id,
                label=label,
                kind="op",
                scope=scope[:-1],
                color="#FFFFFF",
                border="#FF3333",
                shape="box",
            )
            proxy_nodes[scope_path] = proxy
            proxy_ids[scope_path] = node_id
            proxy_id_to_scope[node_id] = scope_path
            return node_id

        def _map_node(node_id: str) -> str:
            node = graph.nodes[node_id]
            if node.kind != "op":
                return node_id
            if not node.scope:
                return node_id
            scope_path = "/".join(node.scope)
            collapsed_scope = self._collapsed_scope_prefix(scope_path)
            if collapsed_scope and not self._is_expanded_path(collapsed_scope):
                if collapsed_scope == "":
                    return ""
                return _proxy_for(collapsed_scope.split("/"))
            if self.effective_depth == 0 and not self._is_expanded_path(scope_path):
                return ""
            if len(node.scope) <= self._visible_depth_for_scope(scope_path):
                return node_id
            scope_prefix = node.scope[: self._visible_depth_for_scope(scope_path) + 1]
            return _proxy_for(scope_prefix)

        visible_ops = set()
        for node in graph.nodes.values():
            if node.kind == "op":
                scope_path = "/".join(node.scope)
                if len(node.scope) <= self._visible_depth_for_scope(scope_path):
                    visible_ops.add(node.node_id)

        visible_nodes = set(visible_ops)
        filtered_edges = []
        proxy_self_counts: Dict[str, int] = {}
        for edge in graph.iter_edges():
            if graph.root_id:
                if edge.src == graph.root_id or edge.dst == graph.root_id:
                    if collapsed_top_scope:
                        continue
                    if (self.max_depth > 0 or expanded_root) and not collapsed_root and not graph.root_is_leaf:
                        continue
            if edge.src not in graph.nodes or edge.dst not in graph.nodes:
                continue
            if collapsed_top_scope and graph.root_id:
                proxy_id = _proxy_for(collapsed_top_scope.split("/"))
                src = proxy_id if edge.src == graph.root_id else _map_node(edge.src)
                dst = proxy_id if edge.dst == graph.root_id else _map_node(edge.dst)
            else:
                src = _map_node(edge.src)
                dst = _map_node(edge.dst)
            if not src or not dst:
                continue
            if src == dst and src.startswith("proxy_"):
                proxy_self_counts[src] = proxy_self_counts.get(src, 0) + 1
                continue
            if self.effective_depth == 0:
                if (src.startswith("proxy_") or dst.startswith("proxy_")):
                    continue
            if src not in graph.nodes and src not in proxy_ids.values():
                continue
            if dst not in graph.nodes and dst not in proxy_ids.values():
                continue
            filtered_edges.append(GraphEdge(src=src, dst=dst, label=edge.label))
            visible_nodes.add(src)
            visible_nodes.add(dst)

        for node in graph.nodes.values():
            if node.node_id not in visible_nodes:
                continue
            if node.kind == "root" and (self.max_depth > 0 or expanded_root) and not (collapsed_root or collapsed_top_scope) and not graph.root_is_leaf:
                continue
            if node.kind == "root" and collapsed_top_scope:
                continue
            if node.kind == "op":
                subgraph = self._ensure_scope(node.scope)
                self._add_node(subgraph, node)
            else:
                self._add_node(self.graph, node)

        for proxy in proxy_nodes.values():
            if proxy.node_id not in visible_nodes:
                continue
            if self.effective_depth == 0:
                continue
            subgraph = self._ensure_scope(proxy.scope)
            self._add_node(subgraph, proxy)

        scope_reps: Dict[str, str] = {}
        for node in graph.nodes.values():
            if node.kind != "op":
                continue
            scope_path = "/".join(node.scope)
            if scope_path and scope_path not in scope_reps:
                scope_reps[scope_path] = node.node_id

        for scope_path, repeat_count in graph.module_repeats.items():
            if repeat_count <= 1:
                continue
            if self.effective_depth == 0:
                continue
            depth = 0 if not scope_path else scope_path.count("/") + 1
            if depth > self._visible_depth_for_scope(scope_path):
                continue
            if scope_path not in self.graph_stack:
                continue
            safe = re.sub(r"[^a-zA-Z0-9_]", "_", scope_path)
            loop_id = f"loop_{safe}"
            cluster = self.graph_stack[scope_path]
            cluster.node(loop_id, label="", shape="point", width="0.01", height="0.01", margin="0", fixedsize="true")
            cluster.edge(loop_id, loop_id, label=f" [ x{repeat_count} ]", tailport="e", headport="e")
            rep_id = scope_reps.get(scope_path)
            if rep_id:
                rank = Digraph()
                rank.attr(rank="same")
                rank.node(rep_id)
                rank.node(loop_id)
                cluster.subgraph(rank)
                cluster.edge(rep_id, loop_id, style="invis", weight="10")

        if self.effective_depth > 0:
            for proxy_id, count in proxy_self_counts.items():
                scope_path = proxy_id_to_scope.get(proxy_id, "")
                if self._collapsed_top_scope and (scope_path == self._collapsed_top_scope or scope_path.startswith(self._collapsed_top_scope + "/")):
                    continue
                repeat_count = graph.module_repeats.get(scope_path, 0)
                if repeat_count > 1:
                    filtered_edges.append(GraphEdge(src=proxy_id, dst=proxy_id, label=f" [ x{repeat_count} ]"))


        self._attach_subgraphs()

        for edge in filtered_edges:
            self.graph.edge(edge.src, edge.dst, label=edge.label)

        self.proxy_id_to_scope = proxy_id_to_scope

    def _ensure_scope(self, scope: List[str]) -> Digraph:
        if not scope:
            return self.graph
        full = ""
        parent = self.graph
        parent_path = ""
        for depth, name in enumerate(scope):
            scope_path = f"{full}/{name}" if full else name
            if depth >= self._visible_depth_for_scope(scope_path) and not self._is_expanded_path(scope_path):
                return parent
            full = f"{full}/{name}" if full else name
            if full not in self.graph_stack:
                safe = re.sub(r"[^a-zA-Z0-9_]", "_", full)
                sub = Digraph(name=f"cluster_{safe}")
                self.cluster_map[f"cluster_{safe}"] = full
                label = name
                if self.graph_data and full in self.graph_data.clusters:
                    label = self.graph_data.clusters[full]
                border_color = "#3399FF" if self.graph_data and full in self.graph_data.module_repeats else "#66AA66"
                sub.attr(label=label, color=border_color, fontsize="11", style="dashed")
                self.graph_stack[full] = sub
                self.graph_parents[full] = parent_path
            parent = self.graph_stack[full]
            parent_path = full
        return parent

    def _is_expanded_path(self, scope_path: str) -> bool:
        return scope_path in self.expand_scopes

    def _is_collapsed_path(self, scope_path: str) -> bool:
        return self._collapsed_scope_prefix(scope_path) != ""

    def _collapsed_scope_prefix(self, scope_path: str) -> str:
        if self._collapsed_top_scope and (scope_path == self._collapsed_top_scope or scope_path.startswith(self._collapsed_top_scope + "/")):
            return self._collapsed_top_scope
        if "" in self.collapse_scopes:
            return ""
        matches = []
        for collapsed in self.collapse_scopes:
            if not collapsed:
                continue
            if scope_path == collapsed or scope_path.startswith(collapsed + "/"):
                matches.append(collapsed)
        if not matches:
            return ""
        return max(matches, key=len)

    def _visible_depth_for_scope(self, scope_path: str) -> int:
        depth = self.effective_depth
        extra = 0
        for expanded in self.expand_scopes:
            if expanded and (scope_path == expanded or scope_path.startswith(expanded + "/")):
                extra += 1
        depth += extra
        if "" in self.collapse_scopes:
            depth = min(depth, 0)
        collapsed_depth = None
        for collapsed in self.collapse_scopes:
            if collapsed and (scope_path == collapsed or scope_path.startswith(collapsed + "/")):
                depth_at = max(collapsed.count("/") + 1 - 1, 0)
                collapsed_depth = depth_at if collapsed_depth is None else min(collapsed_depth, depth_at)
        if collapsed_depth is not None:
            depth = min(depth, collapsed_depth)
        return depth

    def _add_node(self, graph: Digraph, node: GraphNode) -> None:
        graph.node(
            node.node_id,
            label=node.label,
            penwidth="2",
            style="filled, rounded",
            fillcolor="white",
            fontname="Courier New",
            shape="box", #"Mrecord",
            color=node.border,
        )
        self.rendered_nodes.append(node.node_id)
        self.node_display_names[node.node_id] = self._label_to_display(node.label, node.node_id)

    def _label_to_display(self, label: str, fallback: str) -> str:
        if not label:
            return fallback
        match = re.search(r"<font[^>]*>([^<]+)</font>", label)
        if match:
            text = match.group(1).strip()
            if " D@" in text:
                return text.split(" D@", 1)[0].strip()
            return text
        if " D@" in label:
            return label.split(" D@", 1)[0].strip()
        return fallback

    def _attach_subgraphs(self) -> None:
        paths = [p for p in self.graph_stack.keys() if p]
        paths.sort(key=lambda p: p.count("/"), reverse=True)
        for path in paths:
            parent_path = self.graph_parents.get(path, "")
            if parent_path:
                parent = self.graph_stack[parent_path]
                parent.subgraph(self.graph_stack[path])
        for path in paths:
            if self.graph_parents.get(path, "") == "":
                self.graph.subgraph(self.graph_stack[path])


    def export(self) -> None:
        if self.graph is None:
            self.draw(self.max_depth)
        if self.graph is None:
            return
        self.graph.render(self.graph_path, format=self.export_format, cleanup=True)
