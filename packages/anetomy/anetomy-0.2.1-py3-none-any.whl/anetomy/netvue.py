import inspect
from functools import wraps
from typing import Iterable, Mapping

import torch
from torch import nn

from .func_manager import FuncManager
from .network_renderer import NetGraph, Renderer


class NetVue:
    def __init__(self, graph_path: str = "./anetomy.png") -> None:
        if graph_path.endswith(".png"):
            export_format = "png"
        elif graph_path.endswith(".svg"):
            export_format = "svg"
        else:
            raise NameError("ANETOMY ERROR: graph path must be .png or .svg")
        self.graph = NetGraph()
        self.viewer = Renderer(graph_path, export_format)
        self.func_manager = FuncManager()
        self.scope_stack = []
        self.frame_stack = []
        self.active_modules = []
        self._hook_handles = []
        self._enabled = False
        self._with_kwargs = self._detect_with_kwargs()
        self._input_nodes = {}
        self._output_nodes = []
        self._tensor_producer = {}
        self._main_name = "Model"
        self._main_module_id = None
        self._op_seq = {}
        self._module_seq = {}
        self._leaf_nodes = {}
        self._module_scope_counts = {}
        self._scope_op_index = {}
        self._scope_op_order = {}
        self._scope_op_type_counts = {}
        self._op_repeat_counts = {}
        self._op_base_labels = {}
        self._func_depth = 0
        self._scope_repeat = {}
        self._scalar_input_nodes = {}
        self._external_scalar_ids = set()

    def dissect(self, net: nn.Module, *dummy_args, **dummy_kwargs) -> None:
        self.graph = NetGraph()
        self.viewer.graph_data = self.graph
        self.scope_stack = []
        self.frame_stack = []
        self.active_modules = []
        self._hook_handles = []
        self._input_nodes = {}
        self._output_nodes = []
        self._tensor_producer = {}
        self._main_name = net.__class__.__name__
        self._main_module_id = id(net)
        self.graph.root_is_leaf = False
        self.graph.add_root(self._format_label(self._main_name, 0, None))
        self._op_seq = {}
        self._module_seq = {}
        self._leaf_nodes = {}
        self._module_scope_counts = {}
        self._scope_op_index = {}
        self._scope_op_order = {}
        self._scope_op_type_counts = {}
        self._op_repeat_counts = {}
        self._op_base_labels = {}
        self._func_depth = 0
        self._scope_repeat = {}
        self._scalar_input_nodes = {}
        self._external_scalar_ids = set()
        self._enabled = True

        self.func_manager.decorate(self._wrap_function)
        net.apply(self._register_hook)
        try:
            self._register_external_inputs(dummy_args, dummy_kwargs)
            outputs = net(*dummy_args, **dummy_kwargs)
        finally:
            self.func_manager.undecorate()
            self._remove_hooks()
            self._enabled = False
        self._record_outputs_for_main(outputs)

    def render(self, max_depth: int = 0) -> None:
        self.viewer.draw(max_depth, self.graph)
        self.viewer.export()

    def launch(self, host: str = "127.0.0.1", port: int = 7880, max_depth: int = 0) -> None:
        self.viewer.draw(max_depth, self.graph)
        self.viewer.launch(host, port)

    def _detect_with_kwargs(self) -> bool:
        sig = inspect.signature(nn.Module.register_forward_pre_hook)
        return "with_kwargs" in sig.parameters

    def _register_hook(self, module: nn.Module) -> None:
        if getattr(module, "_anetomy_hooked", False):
            return
        module._anetomy_hooked = True
        if self._with_kwargs:
            self._hook_handles.append(module.register_forward_pre_hook(self._before_forward, with_kwargs=True))
            self._hook_handles.append(module.register_forward_hook(self._after_forward, with_kwargs=True))
        else:
            self._hook_handles.append(module.register_forward_pre_hook(self._before_forward))
            self._hook_handles.append(module.register_forward_hook(self._after_forward))

    def _remove_hooks(self) -> None:
        for handle in self._hook_handles:
            handle.remove()
        self._hook_handles = []

    def _wrap_function(self, pkg_name, func_name, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self._enabled:
                return func(*args, **kwargs)
            if self._func_depth > 0:
                return func(*args, **kwargs)
            parent = self._current_frame()
            if (
                parent is not None
                and parent["is_builtin"]
                and not parent.get("has_submodules", False)
                and not parent.get("allow_func_ops", False)
            ):
                return func(*args, **kwargs)
            scope_path = self._scope_path(self.scope_stack)
            skip_edges = self._scope_repeat.get(scope_path, False)
            depth = len(self.scope_stack)
            if pkg_name == "torch.Tensor" and func_name == "__getitem__":
                index = args[1] if len(args) > 1 else None
                if index is None:
                    return func(*args, **kwargs)
                attrs = self._index_attrs(index)
            else:
                attrs = self._func_attrs(func_name, args, kwargs)
            if parent is not None:
                parent["has_children"] = True
            op_func_name = func_name
            if pkg_name == "torch.Tensor" and func_name == "__getitem__":
                op_func_name = "slice" if self._is_slice_index(index) else "index"
            op_id = None
            if scope_path in self._scope_op_index:
                op_id, _ = self._get_scoped_op(scope_path, op_func_name, depth, attrs)
            else:
                op_label = self._next_op_name(op_func_name)
                label = self._format_label(op_label, depth, attrs)
                op_id = self.graph.add_op(op_label, label, scope=list(self.scope_stack), color="#FF3333", border="#FF3333")
                self._op_base_labels[op_id] = label
                self._op_repeat_counts[op_id] = 0
            if parent is None:
                self._increment_op_repeat(op_id)
                if not skip_edges:
                    self._record_inputs(op_id, args, kwargs)
            else:
                if not skip_edges and not parent["is_repeat"]:
                    count = parent["op_counts"].get(op_id, 0) + 1
                    parent["op_counts"][op_id] = count
                    self._set_op_repeat(op_id, count)
                    if count == 1:
                        self._record_inputs(op_id, args, kwargs)
                    self._update_consecutive(parent, op_id)
            self._func_depth += 1
            try:
                out = func(*args, **kwargs)
            finally:
                self._func_depth = max(self._func_depth - 1, 0)
            self._record_outputs(op_id, out)
            return out
        return wrapper

    def _before_forward(self, module: nn.Module, args, kwargs=None):
        if not self._enabled:
            return args if kwargs is None else (args, kwargs)

        scope_name = self._module_call_name(module)
        total = getattr(module, "_anetomy_total_count", 0)
        is_non_param = all(p.numel() == 0 for p in module.parameters(recurse=False))
        is_repeat = total > 0 and not is_non_param
        module._anetomy_total_count = total + 1
        is_builtin = module.__class__.__module__.startswith("torch.nn")
        scope_path = self._scope_path(self.scope_stack + [scope_name])
        depth = len(self.scope_stack)
        self._scope_op_index[scope_path] = 0
        self._scope_repeat[scope_path] = is_repeat
        frame = {
            "module": module,
            "scope": scope_name,
            "scope_path": scope_path,
            "depth": depth,
            "is_builtin": is_builtin,
            "is_repeat": is_repeat,
            "is_non_param": is_non_param,
            "has_submodules": any(True for _ in module.children()),
            "allow_func_ops": isinstance(module, (nn.RNNCellBase, nn.MultiheadAttention)),
            "inputs": list(self._collect_tensors(args)) + list(self._collect_tensors(kwargs)),
            "has_children": False,
            "op_counts": {},
            "last_op_id": None,
            "last_op_run": 0,
        }
        if self.frame_stack:
            self.frame_stack[-1]["has_children"] = True
        self.frame_stack.append(frame)
        self.scope_stack.append(scope_name)
        self.active_modules.append(module)
        return args if kwargs is None else (args, kwargs)

    def _after_forward(self, module: nn.Module, args, kwargs_or_out, out=None):
        if not self._enabled:
            return out if out is not None else kwargs_or_out
        outputs = kwargs_or_out if out is None else out
        frame = self.frame_stack.pop() if self.frame_stack else None
        if self.scope_stack:
            self.scope_stack.pop()
        if self.active_modules:
            self.active_modules.pop()
        if frame is None:
            return outputs
        if not frame["has_children"]:
            depth = frame["depth"]
            attrs = self._module_attrs(frame["module"])
            is_non_param = frame.get("is_non_param", False)
            label = self._format_label(frame["scope"], depth, attrs)
            scope = list(self.scope_stack)
            if id(frame["module"]) == self._main_module_id and self.graph.root_id:
                self.graph.nodes[self.graph.root_id].label = self._format_label(self._main_name, 0, attrs)
                self.graph.root_is_leaf = True
                self._record_outputs(self.graph.root_id, outputs)
                return outputs
            op_id = None
            if not is_non_param:
                key = (id(frame["module"]), self._scope_path(scope))
                op_id = self._leaf_nodes.get(key)
            if op_id is None:
                op_label = frame["scope"]
                if is_non_param:
                    op_label = self._next_op_name(frame["scope"])
                    label = self._format_label(op_label, depth, attrs)
                op_id = self.graph.add_op(op_label, label, scope=scope, color="#FF3333", border="#FF3333")
                if not is_non_param:
                    self._leaf_nodes[key] = op_id
            parent = self._current_frame()
            if parent is not None and not parent["is_repeat"]:
                count = parent["op_counts"].get(op_id, 0) + 1
                parent["op_counts"][op_id] = count
                self._set_op_repeat(op_id, count)
                if count == 1 and (not frame["is_repeat"] or is_non_param):
                    self._record_inputs(op_id, frame["inputs"], None)
                self._update_consecutive(parent, op_id)
            else:
                count = getattr(frame["module"], "_anetomy_leaf_count", 0) + 1
                frame["module"]._anetomy_leaf_count = count
                self._update_repeat_label(op_id, label, count)
                if not frame["is_repeat"]:
                    self._record_inputs(op_id, frame["inputs"], None)
            self._record_outputs(op_id, outputs)
        else:
            count = self._module_scope_counts.get(frame["scope_path"], 0) + 1
            self._module_scope_counts[frame["scope_path"]] = count
            if count > 1:
                self.graph.set_cluster_label(frame["scope_path"], f"{frame['scope']}", repeat_count=count)
            if not frame["is_repeat"]:
                self._flush_consecutive(frame)
        if not frame["is_repeat"]:
            self._flush_consecutive(frame)
        self._scope_op_index.pop(frame["scope_path"], None)
        self._scope_repeat.pop(frame["scope_path"], None)
        return outputs

    def _module_call_name(self, module: nn.Module) -> str:
        base = module.__class__.__name__
        if not hasattr(module, "_anetomy_inst_name"):
            module._anetomy_inst_name = f"{base}_{self._next_module_id(base)}"
        base_name = module._anetomy_inst_name
        return base_name

    def _record_inputs(self, op_id: str, args, kwargs):
        seen = set()
        for item in self._collect_items(args):
            if isinstance(item, torch.Tensor):
                tid = id(item)
                if tid in seen:
                    continue
                seen.add(tid)
                src = self._tensor_producer.get(tid)
                if src is None:
                    src = self._get_input_node(item)
                    self._tensor_producer[tid] = src
                self.graph.add_edge(src, op_id, self._shape_str(item))
            elif self._is_external_scalar(item):
                sid = id(item)
                if sid in seen:
                    continue
                seen.add(sid)
                src = self._get_scalar_input_node(item)
                self.graph.add_edge(src, op_id, "1")
        for item in self._collect_items(kwargs):
            if isinstance(item, torch.Tensor):
                tid = id(item)
                if tid in seen:
                    continue
                seen.add(tid)
                src = self._tensor_producer.get(tid)
                if src is None:
                    src = self._get_input_node(item)
                    self._tensor_producer[tid] = src
                self.graph.add_edge(src, op_id, self._shape_str(item))
            elif self._is_external_scalar(item):
                sid = id(item)
                if sid in seen:
                    continue
                seen.add(sid)
                src = self._get_scalar_input_node(item)
                self.graph.add_edge(src, op_id, str(item))

    def _record_outputs(self, op_id: str, outputs):
        for tensor in self._collect_tensors(outputs):
            self._tensor_producer[id(tensor)] = op_id

    def _record_outputs_for_main(self, outputs):
        for tensor in self._collect_tensors(outputs):
            out_id = self.graph.add_io(self._format_label(f"{self._main_name}@output_{len(self._output_nodes)}", 
                                                            0, None, '#F0F0FF', 'black'))
            self._output_nodes.append(out_id)
            producer = self._tensor_producer.get(id(tensor))
            if producer is None:
                producer = self._get_input_node(tensor)
            self.graph.add_edge(producer, out_id, self._shape_str(tensor))
            if self.graph.root_id:
                self.graph.add_edge(self.graph.root_id, out_id, self._shape_str(tensor))

    def _get_input_node(self, tensor) -> str:
        tid = id(tensor)
        if tid in self._input_nodes:
            return self._input_nodes[tid]
        node_id = self.graph.add_io(self._format_label(f"{self._main_name}@input_{self._next_input_index()}", 
                                                        0, None, '#F0F0FF', 'black'))
        self._input_nodes[tid] = node_id
        if self.graph.root_id:
            self.graph.add_edge(node_id, self.graph.root_id, self._shape_str(tensor))
        return node_id

    def _get_scalar_input_node(self, value) -> str:
        vid = id(value)
        if vid in self._scalar_input_nodes:
            return self._scalar_input_nodes[vid]
        node_id = self.graph.add_io(self._format_label(f"{self._main_name}@input_{self._next_input_index()}", 
                                                        0, None, '#F0F0FF', 'black'))
        self._scalar_input_nodes[vid] = node_id
        if self.graph.root_id:
            self.graph.add_edge(node_id, self.graph.root_id, "1")
        return node_id

    def _next_input_index(self) -> int:
        return len(self._input_nodes) + len(self._scalar_input_nodes)

    def _shape_str(self, tensor) -> str:
        if not hasattr(tensor, "shape"):
            return ""
        shape = list(tensor.shape)
        if not shape:
            return "1"
        return " x ".join(str(dim) for dim in shape)

    def _collect_tensors(self, item):
        if item is None:
            return []
        if isinstance(item, torch.Tensor):
            return [item]
        if isinstance(item, Mapping):
            out = []
            for val in item.values():
                out.extend(self._collect_tensors(val))
            return out
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            out = []
            for val in item:
                out.extend(self._collect_tensors(val))
            return out
        return []

    def _collect_items(self, item):
        if item is None:
            return []
        if isinstance(item, torch.Tensor):
            return [item]
        if isinstance(item, Mapping):
            out = []
            for val in item.values():
                out.extend(self._collect_items(val))
            return out
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            out = []
            for val in item:
                out.extend(self._collect_items(val))
            return out
        return [item]

    def _format_label(self, name: str, depth: int, attrs, bg='black', fg='white'):
        if attrs:
            body = "\n".join([f'<tr><td align="left" port="r5">{a}</td></tr>' for a in attrs])
            return f"""<
                        <table border="0" cellborder="0" cellpadding="3" bgcolor="white">
                            <tr>
                                <td bgcolor="{bg}" align="center" colspan="2"><font color="{fg}">{name} D@{depth}</font></td>
                            </tr>
                            {body}
                        </table>
                    >"""
        return f"""<
                    <table border="0" cellborder="0" cellpadding="3" bgcolor="white">
                        <tr>
                            <td bgcolor="{bg}" align="center" colspan="2"><font color="{fg}">{name} D@{depth}</font></td>
                        </tr>
                    </table>
                >"""

    def _module_attrs(self, module: nn.Module):
        if isinstance(module, (nn.Conv1d, nn.Conv2d, nn.Conv3d)):
            return [
                f"In Chs: {module.in_channels}",
                f"Out Chs: {module.out_channels}",
                f"Kernel: {self._fmt_tuple(module.kernel_size)}",
                f"Stride: {self._fmt_tuple(module.stride)}",
                f"Pad: {self._fmt_tuple(module.padding)}",
                f"Dilation: {self._fmt_tuple(module.dilation)}",
                f"Group: {module.groups}",
            ]
        if isinstance(module, (nn.ConvTranspose1d, nn.ConvTranspose2d, nn.ConvTranspose3d)):
            return [
                f"In Chs: {module.in_channels}",
                f"Out Chs: {module.out_channels}",
                f"Kernel: {self._fmt_tuple(module.kernel_size)}",
                f"Stride: {self._fmt_tuple(module.stride)}",
                f"Pad: {self._fmt_tuple(module.padding)}",
                f"Out Pad: {self._fmt_tuple(module.output_padding)}",
                f"Dilation: {self._fmt_tuple(module.dilation)}",
                f"Group: {module.groups}",
            ]
        if isinstance(module, (nn.MaxPool1d, nn.MaxPool2d, nn.MaxPool3d, nn.AvgPool1d, nn.AvgPool2d, nn.AvgPool3d)):
            return [
                f"Kernel: {self._fmt_tuple(module.kernel_size)}",
                f"Stride: {self._fmt_tuple(module.stride)}",
                f"Pad: {self._fmt_tuple(module.padding)}",
            ]
        if isinstance(module, (nn.AdaptiveAvgPool1d, nn.AdaptiveAvgPool2d, nn.AdaptiveAvgPool3d)):
            return [f"Out Size: {self._fmt_tuple(module.output_size)}"]
        if isinstance(module, (nn.AdaptiveMaxPool1d, nn.AdaptiveMaxPool2d, nn.AdaptiveMaxPool3d)):
            return [f"Out Size: {self._fmt_tuple(module.output_size)}"]
        if isinstance(module, nn.Linear):
            return [
                f"In Chs: {module.in_features}",
                f"Out Chs: {module.out_features}",
            ]
        if isinstance(module, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)):
            return [
                f"Num Feat: {module.num_features}",
                f"Affine: {module.affine}",
                f"Track: {module.track_running_stats}",
            ]
        if isinstance(module, nn.GroupNorm):
            return [
                f"Groups: {module.num_groups}",
                f"Chs: {module.num_channels}",
                f"Affine: {module.affine}",
            ]
        if isinstance(module, nn.LayerNorm):
            return [
                f"Shape: {self._fmt_tuple(module.normalized_shape)}",
                f"Affine: {module.elementwise_affine}",
            ]
        if isinstance(module, (nn.InstanceNorm1d, nn.InstanceNorm2d, nn.InstanceNorm3d)):
            return [
                f"Num Feat: {module.num_features}",
                f"Affine: {module.affine}",
                f"Track: {module.track_running_stats}",
            ]
        if isinstance(module, (nn.Dropout, nn.Dropout2d, nn.Dropout3d, nn.AlphaDropout)):
            return [f"Prob: {module.p}"]
        try:
            from torchvision.ops import StochasticDepth
        except Exception:
            StochasticDepth = None
        if StochasticDepth is not None and isinstance(module, StochasticDepth):
            return [
                f"Prob: {module.p}",
                f"Mode: {module.mode}",
            ]
        try:
            from torchvision.ops import DeformConv2d
        except Exception:
            DeformConv2d = None
        if DeformConv2d is not None and isinstance(module, DeformConv2d):
            return [
                f"In Chs: {module.in_channels}",
                f"Out Chs: {module.out_channels}",
                f"Kernel: {self._fmt_tuple(module.kernel_size)}",
                f"Stride: {self._fmt_tuple(module.stride)}",
                f"Pad: {self._fmt_tuple(module.padding)}",
                f"Dilation: {self._fmt_tuple(module.dilation)}",
                f"Group: {module.groups}",
            ]
        if isinstance(module, nn.Embedding):
            return [
                f"Num: {module.num_embeddings}",
                f"Dim: {module.embedding_dim}",
            ]
        if isinstance(module, nn.MultiheadAttention):
            return [
                f"Embed: {module.embed_dim}",
                f"Heads: {module.num_heads}",
                f"Batch First: {module.batch_first}",
            ]
        if isinstance(module, (nn.RNN, nn.GRU, nn.LSTM)):
            return [
                f"In Size: {module.input_size}",
                f"Hid Size: {module.hidden_size}",
                f"Layers: {module.num_layers}",
                f"Bi: {module.bidirectional}",
            ]
        return []

    def _func_attrs(self, func_name: str, args, kwargs):
        if func_name in {"relu", "gelu", "silu", "sigmoid", "tanh"}:
            return []
        if func_name in {"cat", "stack"}:
            axis = None
            if len(args) > 1:
                axis = args[1]
            elif kwargs and "dim" in kwargs:
                axis = kwargs.get("dim")
            axis_str = self._axis_str(axis)
            return [f"Axis: {axis_str}"]
        if func_name in {"reshape", "view"}:
            shape = None
            if len(args) > 1:
                shape = args[1:]
            elif kwargs and "shape" in kwargs:
                shape = kwargs.get("shape")
            if shape is not None:
                return [f"Axis: {self._axis_str(shape)}"]
        if func_name == "flatten":
            start_dim = 0
            end_dim = -1
            if len(args) > 1:
                start_dim = args[1]
            if len(args) > 2:
                end_dim = args[2]
            if kwargs:
                start_dim = kwargs.get("start_dim", start_dim)
                end_dim = kwargs.get("end_dim", end_dim)
            return [f"Axis: {self._axis_str([start_dim, end_dim])}"]
        if func_name in {"permute", "transpose"}:
            dims = None
            if len(args) > 1:
                dims = args[1:]
            if dims is not None:
                return [f"Axis: {self._axis_str(dims)}"]
        if func_name in {"softmax", "log_softmax"}:
            dim = kwargs.get("dim") if kwargs else None
            if dim is None and len(args) > 1:
                dim = args[1]
            return [f"Dim: {self._axis_str(dim)}"]
        if func_name in {"dropout", "dropout2d", "dropout3d", "alpha_dropout"}:
            p = kwargs.get("p") if kwargs else None
            if p is None and len(args) > 1:
                p = args[1]
            return [f"Prob: {p}"] if p is not None else []
        if func_name in {"conv1d", "conv2d", "conv3d"}:
            weight = args[1] if len(args) > 1 else None
            attrs = []
            if isinstance(weight, torch.Tensor) and weight.ndim >= 3:
                out_ch = weight.shape[0]
                in_ch = weight.shape[1]
                kernel = weight.shape[2:]
                attrs.extend([f"In Chs: {in_ch}", f"Out Chs: {out_ch}", f"Kernel: {self._fmt_tuple(kernel)}"])
            stride = kwargs.get("stride") if kwargs else None
            padding = kwargs.get("padding") if kwargs else None
            dilation = kwargs.get("dilation") if kwargs else None
            groups = kwargs.get("groups") if kwargs else None
            if stride is not None:
                attrs.append(f"Stride: {self._fmt_tuple(stride)}")
            if padding is not None:
                attrs.append(f"Pad: {self._fmt_tuple(padding)}")
            if dilation is not None:
                attrs.append(f"Dilation: {self._fmt_tuple(dilation)}")
            if groups is not None:
                attrs.append(f"Group: {groups}")
            return attrs
        if func_name == "linear":
            weight = args[1] if len(args) > 1 else None
            if isinstance(weight, torch.Tensor) and weight.ndim == 2:
                return [f"In Chs: {weight.shape[1]}", f"Out Chs: {weight.shape[0]}"]
        if func_name in {"max_pool1d", "max_pool2d", "max_pool3d", "avg_pool1d", "avg_pool2d", "avg_pool3d"}:
            kernel = kwargs.get("kernel_size") if kwargs else None
            stride = kwargs.get("stride") if kwargs else None
            padding = kwargs.get("padding") if kwargs else None
            attrs = []
            if kernel is not None:
                attrs.append(f"Kernel: {self._fmt_tuple(kernel)}")
            if stride is not None:
                attrs.append(f"Stride: {self._fmt_tuple(stride)}")
            if padding is not None:
                attrs.append(f"Pad: {self._fmt_tuple(padding)}")
            return attrs
        if func_name in {"adaptive_avg_pool1d", "adaptive_avg_pool2d", "adaptive_avg_pool3d"}:
            output_size = kwargs.get("output_size") if kwargs else None
            if output_size is None and len(args) > 1:
                output_size = args[1]
            return [f"Out Size: {self._fmt_tuple(output_size)}"] if output_size is not None else []
        if func_name in {"adaptive_max_pool1d", "adaptive_max_pool2d", "adaptive_max_pool3d"}:
            output_size = kwargs.get("output_size") if kwargs else None
            if output_size is None and len(args) > 1:
                output_size = args[1]
            return [f"Out Size: {self._fmt_tuple(output_size)}"] if output_size is not None else []
        if func_name in {"conv_transpose1d", "conv_transpose2d", "conv_transpose3d"}:
            weight = args[1] if len(args) > 1 else None
            attrs = []
            if isinstance(weight, torch.Tensor) and weight.ndim >= 3:
                in_ch = weight.shape[0]
                out_ch = weight.shape[1] * (kwargs.get("groups", 1) if kwargs else 1)
                kernel = weight.shape[2:]
                attrs.extend([f"In Chs: {in_ch}", f"Out Chs: {out_ch}", f"Kernel: {self._fmt_tuple(kernel)}"])
            stride = kwargs.get("stride") if kwargs else None
            padding = kwargs.get("padding") if kwargs else None
            output_padding = kwargs.get("output_padding") if kwargs else None
            dilation = kwargs.get("dilation") if kwargs else None
            groups = kwargs.get("groups") if kwargs else None
            if stride is not None:
                attrs.append(f"Stride: {self._fmt_tuple(stride)}")
            if padding is not None:
                attrs.append(f"Pad: {self._fmt_tuple(padding)}")
            if output_padding is not None:
                attrs.append(f"Out Pad: {self._fmt_tuple(output_padding)}")
            if dilation is not None:
                attrs.append(f"Dilation: {self._fmt_tuple(dilation)}")
            if groups is not None:
                attrs.append(f"Group: {groups}")
            return attrs
        if func_name in {"interpolate", "upsample"}:
            size = kwargs.get("size") if kwargs else None
            scale = kwargs.get("scale_factor") if kwargs else None
            mode = kwargs.get("mode") if kwargs else None
            align = kwargs.get("align_corners") if kwargs else None
            attrs = []
            if size is not None:
                attrs.append(f"Size: {self._fmt_tuple(size)}")
            if scale is not None:
                attrs.append(f"Scale: {self._fmt_tuple(scale)}")
            if mode is not None:
                attrs.append(f"Mode: {mode}")
            if align is not None:
                attrs.append(f"Align: {align}")
            return attrs
        if func_name == "pad":
            pad = kwargs.get("pad") if kwargs else None
            mode = kwargs.get("mode") if kwargs else None
            value = kwargs.get("value") if kwargs else None
            attrs = []
            if pad is None and len(args) > 1:
                pad = args[1]
            if pad is not None:
                attrs.append(f"Pad: {self._fmt_tuple(pad)}")
            if mode is not None:
                attrs.append(f"Mode: {mode}")
            if value is not None:
                attrs.append(f"Val: {value}")
            return attrs
        if func_name == "batch_norm":
            eps = kwargs.get("eps") if kwargs else None
            momentum = kwargs.get("momentum") if kwargs else None
            training = kwargs.get("training") if kwargs else None
            attrs = []
            if eps is not None:
                attrs.append(f"Eps: {eps}")
            if momentum is not None:
                attrs.append(f"Mom: {momentum}")
            if training is not None:
                attrs.append(f"Train: {training}")
            return attrs
        if func_name == "layer_norm":
            shape = kwargs.get("normalized_shape") if kwargs else None
            if shape is None and len(args) > 1:
                shape = args[1]
            eps = kwargs.get("eps") if kwargs else None
            attrs = []
            if shape is not None:
                attrs.append(f"Shape: {self._fmt_tuple(shape)}")
            if eps is not None:
                attrs.append(f"Eps: {eps}")
            return attrs
        if func_name == "group_norm":
            num_groups = kwargs.get("num_groups") if kwargs else None
            if num_groups is None and len(args) > 1:
                num_groups = args[1]
            num_channels = kwargs.get("num_channels") if kwargs else None
            if num_channels is None and len(args) > 2:
                num_channels = args[2]
            eps = kwargs.get("eps") if kwargs else None
            attrs = []
            if num_groups is not None:
                attrs.append(f"Groups: {num_groups}")
            if num_channels is not None:
                attrs.append(f"Chs: {num_channels}")
            if eps is not None:
                attrs.append(f"Eps: {eps}")
            return attrs
        if func_name == "instance_norm":
            eps = kwargs.get("eps") if kwargs else None
            momentum = kwargs.get("momentum") if kwargs else None
            affine = kwargs.get("affine") if kwargs else None
            track = kwargs.get("track_running_stats") if kwargs else None
            attrs = []
            if eps is not None:
                attrs.append(f"Eps: {eps}")
            if momentum is not None:
                attrs.append(f"Mom: {momentum}")
            if affine is not None:
                attrs.append(f"Affine: {affine}")
            if track is not None:
                attrs.append(f"Track: {track}")
            return attrs
        if func_name == "normalize":
            p = kwargs.get("p") if kwargs else None
            dim = kwargs.get("dim") if kwargs else None
            eps = kwargs.get("eps") if kwargs else None
            attrs = []
            if p is not None:
                attrs.append(f"p: {p}")
            if dim is not None:
                attrs.append(f"Dim: {self._axis_str(dim)}")
            if eps is not None:
                attrs.append(f"Eps: {eps}")
            return attrs
        if func_name == "grid_sample":
            mode = kwargs.get("mode") if kwargs else None
            padding_mode = kwargs.get("padding_mode") if kwargs else None
            align = kwargs.get("align_corners") if kwargs else None
            attrs = []
            if mode is not None:
                attrs.append(f"Mode: {mode}")
            if padding_mode is not None:
                attrs.append(f"Pad: {padding_mode}")
            if align is not None:
                attrs.append(f"Align: {align}")
            return attrs
        if func_name == "unfold":
            kernel = kwargs.get("kernel_size") if kwargs else None
            stride = kwargs.get("stride") if kwargs else None
            padding = kwargs.get("padding") if kwargs else None
            dilation = kwargs.get("dilation") if kwargs else None
            attrs = []
            if kernel is not None:
                attrs.append(f"Kernel: {self._fmt_tuple(kernel)}")
            if stride is not None:
                attrs.append(f"Stride: {self._fmt_tuple(stride)}")
            if padding is not None:
                attrs.append(f"Pad: {self._fmt_tuple(padding)}")
            if dilation is not None:
                attrs.append(f"Dilation: {self._fmt_tuple(dilation)}")
            return attrs
        if func_name == "fold":
            output_size = kwargs.get("output_size") if kwargs else None
            kernel = kwargs.get("kernel_size") if kwargs else None
            stride = kwargs.get("stride") if kwargs else None
            padding = kwargs.get("padding") if kwargs else None
            dilation = kwargs.get("dilation") if kwargs else None
            attrs = []
            if output_size is not None:
                attrs.append(f"Out Size: {self._fmt_tuple(output_size)}")
            if kernel is not None:
                attrs.append(f"Kernel: {self._fmt_tuple(kernel)}")
            if stride is not None:
                attrs.append(f"Stride: {self._fmt_tuple(stride)}")
            if padding is not None:
                attrs.append(f"Pad: {self._fmt_tuple(padding)}")
            if dilation is not None:
                attrs.append(f"Dilation: {self._fmt_tuple(dilation)}")
            return attrs
        if func_name == "einsum":
            equation = args[0] if args else None
            return [f"Eq: {equation}"] if isinstance(equation, str) else []
        return []

    def _axis_str(self, axis):
        if axis is None:
            return "default(0)"
        if isinstance(axis, torch.Tensor):
            if axis.dim() == 0:
                axis = axis.item()
            else:
                axis = axis.tolist()
        if isinstance(axis, Iterable) and not isinstance(axis, (str, bytes)):
            return ", ".join(str(a) for a in axis)
        return str(axis)

    def _is_slice_index(self, idx) -> bool:
        if isinstance(idx, slice) or idx is Ellipsis:
            return True
        if isinstance(idx, tuple):
            return any(self._is_slice_index(item) for item in idx)
        return False

    def _index_attrs(self, idx):
        return [f"Idx: {self._format_index(idx)}"]

    def _format_index(self, idx) -> str:
        if idx is Ellipsis:
            return "..."
        if isinstance(idx, slice):
            start = "" if idx.start is None else idx.start
            stop = "" if idx.stop is None else idx.stop
            step = "" if idx.step is None else idx.step
            if step != "":
                return f"{start}:{stop}:{step}"
            return f"{start}:{stop}"
        if isinstance(idx, tuple):
            return ", ".join(self._format_index(item) for item in idx)
        if isinstance(idx, torch.Tensor):
            if idx.dim() == 0:
                return str(idx.item())
            shape = "x".join(str(dim) for dim in idx.shape)
            return f"[{shape}] tensor"
        return str(idx)

    def _current_frame(self):
        if not self.frame_stack:
            return None
        return self.frame_stack[-1]

    def _update_consecutive(self, frame, op_id: str) -> None:
        if frame["last_op_id"] == op_id:
            frame["last_op_run"] += 1
            return
        self._flush_consecutive(frame)
        frame["last_op_id"] = op_id
        frame["last_op_run"] = 1

    def _flush_consecutive(self, frame) -> None:
        last_op_id = frame.get("last_op_id")
        run = frame.get("last_op_run", 0)
        if last_op_id and run > 1:
            self.graph.add_edge(last_op_id, last_op_id, f" [ x{run} ]")
        frame["last_op_id"] = None
        frame["last_op_run"] = 0

    def _scope_path(self, scope):
        return "/".join(scope)

    def _update_repeat_label(self, op_id: str, base_label: str, count: int) -> None:
        self.graph.nodes[op_id].label = base_label

    def _increment_op_repeat(self, op_id: str) -> None:
        count = self._op_repeat_counts.get(op_id, 0) + 1
        self._op_repeat_counts[op_id] = count
        base_label = self._op_base_labels.get(op_id, self.graph.nodes[op_id].label)
        self._update_repeat_label(op_id, base_label, count)

    def _set_op_repeat(self, op_id: str, count: int) -> None:
        self._op_repeat_counts[op_id] = max(self._op_repeat_counts.get(op_id, 0), count)
        base_label = self._op_base_labels.get(op_id, self.graph.nodes[op_id].label)
        self._update_repeat_label(op_id, base_label, count)

    def _get_scoped_op(self, scope_path: str, func_name: str, depth: int, attrs):
        idx = self._scope_op_index.get(scope_path, 0)
        order = self._scope_op_order.setdefault(scope_path, [])
        if idx < len(order):
            op_id = order[idx]
            self._scope_op_index[scope_path] = idx + 1
            return op_id, self._op_base_labels.get(op_id, self.graph.nodes[op_id].label)
        type_counts = self._scope_op_type_counts.setdefault(scope_path, {})
        count = type_counts.get(func_name, 0)
        type_counts[func_name] = count + 1
        op_label = f"{func_name}_{count}"
        label = self._format_label(op_label, depth, attrs)
        op_id = self.graph.add_op(op_label, label, scope=scope_path.split("/") if scope_path else [], color="#FF3333", border="#FF3333")
        self._op_base_labels[op_id] = label
        self._op_repeat_counts[op_id] = 0
        order.append(op_id)
        self._scope_op_index[scope_path] = idx + 1
        return op_id, op_label

    def _next_op_name(self, base: str) -> str:
        count = self._op_seq.get(base, 0)
        self._op_seq[base] = count + 1
        return f"{base}_{count}"

    def _next_module_id(self, base: str) -> int:
        count = self._module_seq.get(base, 0)
        self._module_seq[base] = count + 1
        return count

    def _fmt_tuple(self, val):
        if isinstance(val, Iterable) and not isinstance(val, (str, bytes)):
            return ", ".join(str(v) for v in val)
        return str(val)

    def _register_external_inputs(self, args, kwargs) -> None:
        for item in self._collect_items(args):
            if isinstance(item, torch.Tensor):
                self._get_input_node(item)
            elif self._is_scalar(item):
                self._external_scalar_ids.add(id(item))
                self._get_scalar_input_node(item)
        for item in self._collect_items(kwargs):
            if isinstance(item, torch.Tensor):
                self._get_input_node(item)
            elif self._is_scalar(item):
                self._external_scalar_ids.add(id(item))
                self._get_scalar_input_node(item)

    def _is_scalar(self, item) -> bool:
        return isinstance(item, (int, float, bool))

    def _is_external_scalar(self, item) -> bool:
        return self._is_scalar(item) and id(item) in self._external_scalar_ids
