import __future__
import types
import torch


_PROHIBITED = {
    torch.Tensor.__weakref__,
    torch.Tensor.__repr__,
    torch.Tensor.__format__,
    torch.Tensor.__gt__,
    torch.Tensor.__lt__,
    torch.Tensor.__ge__,
    torch.Tensor.__le__,
    torch.Tensor.__eq__,
    torch.Tensor.__ne__,
    torch.Tensor.tolist,
    torch.Tensor.item,
    torch.Tensor.unbind,
    torch.Tensor.has_names,
    torch.Tensor.clone,
    torch.Tensor.size,
    torch.Tensor.numel,
    torch.Tensor.shape,
    torch.Tensor.dim,
}


class FuncManager:
    def __init__(self) -> None:
        self._orig_funcs = {}

    def _iter_function_specs(self):
        func_packages = [
            ("torch", torch, torch.__all__),
            ("torch.functional", torch.functional, torch.functional.__all__),
            ("torch.nn.functional", torch.nn.functional, dir(torch.nn.functional)),
            ("torch.Tensor", torch.Tensor, dir(torch.Tensor)),
            ("torch.linalg", torch.linalg, dir(torch.linalg)),
            ("torch.fft", torch.fft, dir(torch.fft)),
        ]
        if hasattr(torch, "special"):
            func_packages.append(("torch.special", torch.special, dir(torch.special)))

        for pkg_name, pkg, names in func_packages:
            for name in names:
                if pkg is not torch.Tensor:
                    if name.startswith("__"):
                        continue
                    if name[0].isupper():
                        continue
                    if name in {"unique_dim"}:
                        continue
                    if "clone" in name or "identity" in name:
                        continue
                else:
                    func = getattr(pkg, name)
                    if getattr(object, name, None) == func:
                        continue

                func = getattr(pkg, name)
                if isinstance(func, types.ModuleType):
                    continue
                if isinstance(func, getattr(__future__, "_Feature")):
                    continue
                if not callable(func):
                    continue
                if func in _PROHIBITED:
                    continue
                if func in torch.overrides.get_ignored_functions():
                    continue
                yield pkg_name, pkg, name, func

    def decorate(self, wrapper_factory):
        if self._orig_funcs:
            return
        for pkg_name, pkg, name, func in self._iter_function_specs():
            self._orig_funcs[(pkg_name, name)] = func
            try:
                setattr(pkg, name, wrapper_factory(pkg_name, name, func))
            except Exception:
                setattr(pkg, name, func)

    def undecorate(self):
        for (pkg_name, name), func in self._orig_funcs.items():
            pkg = self._resolve_pkg(pkg_name)
            setattr(pkg, name, func)
        self._orig_funcs.clear()

    @staticmethod
    def _resolve_pkg(pkg_name):
        if pkg_name == "torch":
            return torch
        if pkg_name == "torch.functional":
            return torch.functional
        if pkg_name == "torch.nn.functional":
            return torch.nn.functional
        if pkg_name == "torch.Tensor":
            return torch.Tensor
        if pkg_name == "torch.linalg":
            return torch.linalg
        if pkg_name == "torch.fft":
            return torch.fft
        if pkg_name == "torch.special":
            return torch.special
        raise KeyError(f"Unknown package {pkg_name}")
